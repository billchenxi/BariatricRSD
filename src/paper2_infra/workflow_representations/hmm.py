"""R3 — HMM latent-state workflow representation.

Paper 1 conditioned on a single workflow representation: TF-IDF over
phase-transition bigrams, PCA, then k-means over whole videos. Reviewer
iSh9 correctly noted that the K=4/6/8 ablation varies the granularity of
that representation without ever leaving the family, so it cannot show
robustness to *how* workflow is represented. Paper 2A needs at least one
genuinely different family. This is it.

**The model.** A first-order HMM with `n_states` latent workflow states.
The observation at each second is the phase label; the emission matrix
therefore learns which phases characterize which latent state, and the
transition matrix learns how surgeries move between states. Parameters
are fit by Baum-Welch on the training split only.

**Why this family is a better fit than k-means for our thesis.** Paper 1's
central distinction is between a *retrospective oracle* representation
(computed from the whole video, unavailable at inference) and a *causal*
one (computable from the prefix). For k-means that distinction required a
separate prefix-clustering apparatus (`src/brsd_lib/causal_cluster.py`). An
HMM gives both for free from one fitted model:

- **causal** — the filtered posterior `P(z_t | x_{1:t})`, from the forward
  recursion alone. Prefix-only by construction: no quantity from after
  `t` enters the computation. There is no way to leak the future.
- **oracle** — the smoothed posterior `P(z_t | x_{1:T})`, from
  forward-backward, which does use the whole video.

The gap between conditioning on the two is exactly the oracle-to-causal
gap Paper 1 measured, obtained here without a second clustering stage.

**Numerics.** Forward-backward is run with per-timestep scaling rather
than in log space. Surgical videos are ~3,000-6,000 timesteps at 1 fps
and unscaled products underflow float64 within a few hundred steps.
Scaling also yields the log-likelihood for free as the sum of the log
scaling factors, which is what drives the convergence check and the
`select_n_states` model-selection sweep.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("workflow_hmm")

EPS = 1e-300  # guards division by an all-zero scaling factor


# ── Model ───────────────────────────────────────────────────────────────────

@dataclass
class WorkflowHMM:
    """A fitted first-order HMM over phase-label sequences.

    `start` is (K,), `trans` is (K, K) row-stochastic, `emit` is
    (K, n_obs) row-stochastic. `n_obs` is the phase-vocabulary size.
    """
    start: np.ndarray
    trans: np.ndarray
    emit: np.ndarray
    n_states: int
    n_obs: int
    log_likelihood: float = float("nan")
    n_iter_run: int = 0
    converged: bool = False

    def to_dict(self) -> Dict:
        return {
            "start": self.start.tolist(),
            "trans": self.trans.tolist(),
            "emit": self.emit.tolist(),
            "n_states": self.n_states,
            "n_obs": self.n_obs,
            "log_likelihood": self.log_likelihood,
            "n_iter_run": self.n_iter_run,
            "converged": self.converged,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "WorkflowHMM":
        return cls(
            start=np.asarray(d["start"], dtype=np.float64),
            trans=np.asarray(d["trans"], dtype=np.float64),
            emit=np.asarray(d["emit"], dtype=np.float64),
            n_states=int(d["n_states"]),
            n_obs=int(d["n_obs"]),
            log_likelihood=float(d.get("log_likelihood", float("nan"))),
            n_iter_run=int(d.get("n_iter_run", 0)),
            converged=bool(d.get("converged", False)),
        )

    @property
    def n_free_params(self) -> int:
        """Free parameters, accounting for the row-sum-to-one constraints."""
        return ((self.n_states - 1)
                + self.n_states * (self.n_states - 1)
                + self.n_states * (self.n_obs - 1))


# ── Forward / backward with scaling ─────────────────────────────────────────

def forward(model: WorkflowHMM, obs: np.ndarray
            ) -> Tuple[np.ndarray, np.ndarray, float]:
    """Scaled forward recursion.

    Returns `(alpha, scale, loglik)` where `alpha[t]` is the *filtered*
    posterior P(z_t | x_{1:t}) — already normalized by the scaling — and
    `loglik = sum(log(scale))`.

    alpha[t] depends only on observations up to and including t. This is
    the causal representation.
    """
    T = obs.shape[0]
    K = model.n_states
    alpha = np.zeros((T, K), dtype=np.float64)
    scale = np.zeros(T, dtype=np.float64)

    a = model.start * model.emit[:, obs[0]]
    scale[0] = a.sum()
    alpha[0] = a / (scale[0] + EPS)
    for t in range(1, T):
        a = (alpha[t - 1] @ model.trans) * model.emit[:, obs[t]]
        scale[t] = a.sum()
        alpha[t] = a / (scale[t] + EPS)

    loglik = float(np.log(scale + EPS).sum())
    return alpha, scale, loglik


def backward(model: WorkflowHMM, obs: np.ndarray,
             scale: np.ndarray) -> np.ndarray:
    """Scaled backward recursion, using the forward pass's scale factors."""
    T = obs.shape[0]
    K = model.n_states
    beta = np.zeros((T, K), dtype=np.float64)
    beta[T - 1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = (model.trans
                   @ (model.emit[:, obs[t + 1]] * beta[t + 1])) / (scale[t + 1] + EPS)
    return beta


def filtered_posteriors(model: WorkflowHMM, obs: np.ndarray) -> np.ndarray:
    """P(z_t | x_{1:t}) for every t — the **causal** representation.

    Shape (T, n_states). Row t is computable from the prefix ending at t
    and nothing else, so it satisfies the strict prefix-only protocol by
    construction.
    """
    alpha, _, _ = forward(model, obs)
    return alpha


def filtered_phase_probabilities(model: WorkflowHMM,
                                 phase_probabilities: np.ndarray,
                                 initial_posterior: Optional[np.ndarray] = None
                                 ) -> np.ndarray:
    """Filter predicted phase distributions into continuous workflow state.

    Each (T, n_obs) input row is a normalized, prefix-only phase prediction.
    We use ``emit @ probabilities[t]`` as soft evidence: this is a mixture
    observation approximation, not a calibrated generative likelihood for
    a discriminative phase classifier. One-hot rows recover hard filtering.
    Ground-truth phase inputs remain an oracle-input diagnostic even when
    the recursion is prefix-only. The caller must enforce input provenance.

    For streaming, pass the last returned row as ``initial_posterior`` for
    the next chunk of the SAME operation. Omit it at a new operation.
    Empty chunks return shape (0, n_states).
    """
    probabilities = np.asarray(phase_probabilities, dtype=np.float64)
    if probabilities.ndim != 2 or probabilities.shape[1] != model.n_obs:
        raise ValueError("phase_probabilities must have shape (T, n_obs)")
    if (not np.isfinite(probabilities).all() or (probabilities < 0).any()
            or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6,
                               rtol=0)):
        raise ValueError("phase probabilities must be finite, nonnegative and sum to one")
    previous = None
    if initial_posterior is not None:
        previous = np.asarray(initial_posterior, dtype=np.float64)
        if (previous.shape != (model.n_states,)
                or not np.isfinite(previous).all() or (previous < 0).any()
                or not np.isclose(previous.sum(), 1.0, atol=1e-6, rtol=0)):
            raise ValueError("initial_posterior must be a normalized state vector")
    result = np.empty((len(probabilities), model.n_states), dtype=np.float64)
    for t, prediction in enumerate(probabilities):
        prior = model.start if previous is None else previous @ model.trans
        evidence = model.emit @ prediction
        unnormalized = prior * evidence
        mass = unnormalized.sum()
        if not np.isfinite(mass) or mass <= 0:
            raise ValueError("observation has zero or invalid evidence under the HMM")
        previous = unnormalized / mass
        result[t] = previous
    return result


def smoothed_posteriors(model: WorkflowHMM, obs: np.ndarray) -> np.ndarray:
    """P(z_t | x_{1:T}) for every t — the **oracle** representation.

    Shape (T, n_states). Uses the whole video including frames after t,
    so it is only valid as a retrospective upper bound, never as a
    deployable conditioning signal.
    """
    alpha, scale, _ = forward(model, obs)
    beta = backward(model, obs, scale)
    gamma = alpha * beta
    row = gamma.sum(axis=1, keepdims=True)
    return gamma / (row + EPS)


# ── Baum-Welch ──────────────────────────────────────────────────────────────

def fit_hmm(sequences: Sequence[np.ndarray], n_states: int, n_obs: int,
            n_iter: int = 200, tol: float = 1e-4, seed: int = 42,
            smoothing: float = 1e-3, n_restarts: int = 1) -> WorkflowHMM:
    """Fit an HMM by Baum-Welch (EM), keeping the best of `n_restarts` runs.

    EM only finds a local optimum, and on real phase sequences the local
    optima differ enough to break the monotonicity one expects from a
    state-count sweep: a first pass over MB140 scored K=8 well above K=6
    and K=12 well below K=10, which is a symptom of initialization luck
    rather than of model order. `n_restarts > 1` runs EM from independent
    inits and keeps the highest training log-likelihood, which restores
    the expected ordering. Use at least 5 for anything reported.

    `smoothing` is added to every expected count before normalizing. Phase
    vocabularies contain labels that appear in only a handful of videos
    ("Out of body", "Unknown"), and without smoothing those columns
    collapse to exactly zero, after which any validation video containing
    that phase gets zero likelihood and produces NaN posteriors. The
    smoothing keeps every emission strictly positive.

    Convergence is declared when the mean per-sequence log-likelihood
    improves by less than `tol`.
    """
    if n_states < 1:
        raise ValueError(f"n_states must be >= 1, got {n_states}")
    if not sequences:
        raise ValueError("no sequences to fit on")
    if n_restarts < 1:
        raise ValueError(f"n_restarts must be >= 1, got {n_restarts}")

    if n_restarts > 1:
        best = None
        for restart in range(n_restarts):
            candidate = _fit_hmm_once(
                sequences, n_states=n_states, n_obs=n_obs, n_iter=n_iter,
                tol=tol, seed=seed + 1000 * restart, smoothing=smoothing)
            if best is None or candidate.log_likelihood > best.log_likelihood:
                best = candidate
        logger.info("HMM K=%d: best of %d restarts, mean loglik %.3f",
                    n_states, n_restarts, best.log_likelihood / len(sequences))
        return best

    return _fit_hmm_once(sequences, n_states=n_states, n_obs=n_obs,
                         n_iter=n_iter, tol=tol, seed=seed, smoothing=smoothing)


def _fit_hmm_once(sequences: Sequence[np.ndarray], n_states: int, n_obs: int,
                  n_iter: int, tol: float, seed: int,
                  smoothing: float) -> WorkflowHMM:
    """One Baum-Welch run from a single random initialization."""
    rng = np.random.default_rng(seed)
    # Random but near-uniform init: a perfectly uniform init is a saddle
    # point for EM and every state would stay identical forever.
    start = rng.dirichlet(np.ones(n_states) * 10.0)
    trans = rng.dirichlet(np.ones(n_states) * 10.0, size=n_states)
    emit = rng.dirichlet(np.ones(n_obs) * 10.0, size=n_states)
    model = WorkflowHMM(start=start, trans=trans, emit=emit,
                        n_states=n_states, n_obs=n_obs)

    prev_ll = -np.inf
    for iteration in range(1, n_iter + 1):
        start_acc = np.full(n_states, smoothing)
        trans_acc = np.full((n_states, n_states), smoothing)
        emit_acc = np.full((n_states, n_obs), smoothing)
        total_ll = 0.0

        for obs in sequences:
            T = obs.shape[0]
            alpha, scale, ll = forward(model, obs)
            beta = backward(model, obs, scale)
            total_ll += ll

            gamma = alpha * beta
            gamma /= (gamma.sum(axis=1, keepdims=True) + EPS)

            start_acc += gamma[0]
            for k in range(n_obs):
                mask = obs == k
                if mask.any():
                    emit_acc[:, k] += gamma[mask].sum(axis=0)

            if T > 1:
                # xi[t, i, j] ∝ alpha[t,i] * A[i,j] * B[j,o_{t+1}] * beta[t+1,j],
                # summed over t in one vectorized contraction.
                emit_next = model.emit[:, obs[1:]].T          # (T-1, K)
                weighted = emit_next * beta[1:] / (scale[1:, None] + EPS)
                trans_acc += model.trans * (alpha[:-1].T @ weighted)

        model = WorkflowHMM(
            start=start_acc / start_acc.sum(),
            trans=trans_acc / trans_acc.sum(axis=1, keepdims=True),
            emit=emit_acc / emit_acc.sum(axis=1, keepdims=True),
            n_states=n_states, n_obs=n_obs,
            log_likelihood=total_ll, n_iter_run=iteration,
        )

        mean_ll = total_ll / len(sequences)
        improvement = mean_ll - prev_ll
        logger.debug("iter %d: mean loglik %.4f (+%.6f)",
                     iteration, mean_ll, improvement)
        if improvement < tol and iteration > 1:
            model.converged = True
            break
        prev_ll = mean_ll

    logger.info("HMM K=%d fit: %d iterations, mean loglik %.3f, converged=%s",
                n_states, model.n_iter_run,
                model.log_likelihood / len(sequences), model.converged)
    return model


def total_log_likelihood(model: WorkflowHMM,
                         sequences: Sequence[np.ndarray]) -> float:
    """Summed log-likelihood of held-out sequences under a fitted model."""
    return float(sum(forward(model, obs)[2] for obs in sequences))


def select_n_states(train: Sequence[np.ndarray], n_obs: int,
                    candidates: Sequence[int] = (2, 3, 4, 6, 8, 10),
                    val: Optional[Sequence[np.ndarray]] = None,
                    seed: int = 42, n_iter: int = 200,
                    n_restarts: int = 5) -> Dict:
    """Sweep the latent-state count, scoring by BIC and held-out likelihood.

    Reports both because they answer different questions: BIC is computed
    on the training sequences and penalizes parameters, held-out
    likelihood measures whether the extra states actually transfer. When
    they disagree, prefer the held-out number and say so in the writeup.
    """
    n_train_obs = int(sum(s.shape[0] for s in train))
    rows = []
    for k in candidates:
        model = fit_hmm(train, n_states=k, n_obs=n_obs, seed=seed,
                        n_iter=n_iter, n_restarts=n_restarts)
        bic = (-2.0 * model.log_likelihood
               + model.n_free_params * math.log(max(n_train_obs, 2)))
        row = {
            "n_states": k,
            "train_loglik": model.log_likelihood,
            "n_free_params": model.n_free_params,
            "bic": bic,
            "converged": model.converged,
        }
        if val:
            row["val_loglik"] = total_log_likelihood(model, val)
            row["val_loglik_per_frame"] = row["val_loglik"] / max(
                sum(s.shape[0] for s in val), 1)
        rows.append(row)

    best_bic = min(rows, key=lambda r: r["bic"])["n_states"]
    out = {"sweep": rows, "best_by_bic": best_bic}
    if val:
        out["best_by_val_loglik"] = max(
            rows, key=lambda r: r["val_loglik"])["n_states"]
    return out


# ── Workflow-variability measurement ────────────────────────────────────────

def posterior_entropy(posterior: np.ndarray) -> float:
    """Mean per-timestep Shannon entropy of a posterior sequence, in nats.

    High entropy means the model is unsure which workflow state the video
    is in. This is *within-video* uncertainty, not across-video
    variability — see `representation_entropy` for the latter.

    Zero probabilities are masked rather than clipped: 0·log 0 is 0 by
    convention, and clipping to a small epsilon instead leaves a residual
    of order 1e-10 on a confident posterior, which is visible when
    comparing near-deterministic representations.
    """
    p = np.asarray(posterior, dtype=np.float64)
    terms = np.zeros_like(p)
    nz = p > 0
    terms[nz] = p[nz] * np.log(p[nz])
    return float((-terms.sum(axis=1)).mean())


def representation_entropy(video_representations: Sequence[np.ndarray]) -> Dict:
    """Across-video workflow variability H(z) for a set of representations.

    This is the quantity Paper 1's variability-scaling thesis depends on
    and the quantity that must be comparable across datasets and
    representation families before any "more variable benchmark →ceteris
    paribus larger conditioning gain" claim can be made.

    Two numbers are reported:

    - `hard_assignment_entropy` — entropy of the distribution of argmax
      states across videos. Directly comparable to the k-means cluster
      entropy Paper 1 reported, since that representation is hard-assigned.
    - `soft_marginal_entropy` — entropy of the mean posterior across
      videos, which uses the full soft assignment and does not throw away
      the model's uncertainty.

    Both are in nats, and both are also reported normalized by log(K) so
    that representations with different state counts can be compared.
    """
    if not video_representations:
        raise ValueError("no representations provided")

    flat = [np.asarray(r, dtype=np.float64).reshape(-1)
            for r in video_representations]
    K = flat[0].size
    bad = {v.size for v in flat} - {K}
    if bad:
        raise ValueError(
            f"representations have inconsistent dimensionality: expected {K}, "
            f"also saw {sorted(bad)}"
        )
    stacked = np.stack(flat)

    hard = np.bincount(stacked.argmax(axis=1), minlength=K).astype(np.float64)
    hard /= hard.sum()
    soft = stacked.mean(axis=0)
    soft /= soft.sum()

    def H(p: np.ndarray) -> float:
        p = p[p > 0]
        return float(-(p * np.log(p)).sum())

    max_h = math.log(K) if K > 1 else 1.0
    return {
        "n_videos": len(video_representations),
        "n_states": K,
        "hard_assignment_entropy": H(hard),
        "hard_assignment_entropy_normalized": H(hard) / max_h,
        "soft_marginal_entropy": H(soft),
        "soft_marginal_entropy_normalized": H(soft) / max_h,
        "state_occupancy": soft.tolist(),
        "n_states_used": int((hard > 0).sum()),
    }


# ── Label-JSON plumbing ─────────────────────────────────────────────────────

def load_phase_sequences(label_json: Path, split: Optional[str] = None
                         ) -> Tuple[List[str], List[np.ndarray], Dict[str, int]]:
    """Read per-frame phase-id sequences from the shared label schema.

    Returns `(video_ids, sequences, phase_vocab)`. Sequences are the
    per-second phase ids, i.e. the observation sequences the HMM consumes.
    """
    videos = json.loads(Path(label_json).read_text())
    if not isinstance(videos, list):
        raise ValueError(f"{label_json}: expected a list of video records")

    vocab: Dict[str, int] = {}
    ids: List[str] = []
    seqs: List[np.ndarray] = []
    for video in videos:
        if split is not None and video.get("split") != split:
            continue
        vocab = vocab or video["phase_vocab"]
        try:
            seq = np.asarray([vocab[f["phase"]] for f in video["frames"]],
                             dtype=np.int64)
        except KeyError as exc:
            raise ValueError(
                f"{video['video_id']}: phase {exc} absent from phase_vocab"
            ) from exc
        if seq.size == 0:
            logger.warning("%s has no frames; skipped", video["video_id"])
            continue
        ids.append(video["video_id"])
        seqs.append(seq)
    return ids, seqs, vocab


def video_representation(model: WorkflowHMM, obs: np.ndarray,
                         mode: str = "causal",
                         at_frame: Optional[int] = None) -> np.ndarray:
    """One video's K-dim workflow *descriptor*, for cross-video comparison.

    Note the distinction from the per-clip conditioning signal. The signal
    the model consumes at prediction time t is a single row of
    `filtered_posteriors(model, obs)[t]` — strictly prefix-only. This
    function instead produces a whole-video summary, which is what the
    entropy and cross-representation comparisons need, since k-means also
    describes a whole video.

    - `mode="causal"` averages the *filtered* posteriors over the video.
      Every frame contributes only its own prefix, so no frame's
      contribution leaks its future, but the average is still a
      whole-video quantity.
    - `mode="oracle"` averages the *smoothed* posteriors, where each
      frame's value already used the whole video. This is the
      retrospective upper bound.

    Passing `at_frame` returns the filtered posterior at that single
    frame instead — the conditioning signal as of that moment.

    A previous version defaulted `mode="causal"` to the *last* frame's
    filtered posterior. That collapsed on stereotyped procedures: every
    Cholec80 video ends in the same phase, so all 72 videos received an
    identical descriptor and H(z) measured exactly 0. Averaging over the
    video is the meaningful summary.
    """
    if mode not in ("causal", "oracle"):
        raise ValueError(f"mode must be 'causal' or 'oracle', got {mode!r}")

    if at_frame is not None:
        if mode != "causal":
            raise ValueError(
                "at_frame is only meaningful for mode='causal'; the oracle "
                "descriptor is a whole-video quantity by construction")
        alpha = filtered_posteriors(model, obs)
        if not 0 <= at_frame < alpha.shape[0]:
            raise IndexError(
                f"at_frame={at_frame} outside the video's {alpha.shape[0]} frames")
        return alpha[at_frame]

    if mode == "causal":
        return filtered_posteriors(model, obs).mean(axis=0)
    return smoothed_posteriors(model, obs).mean(axis=0)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--label-json", required=True, type=Path)
    ap.add_argument("--n-states", type=int, default=6,
                    help="Latent workflow states. Ignored when --sweep is set.")
    ap.add_argument("--sweep", type=int, nargs="*", default=None,
                    help="Candidate state counts to sweep instead of fitting one.")
    ap.add_argument("--train-split", default="train")
    ap.add_argument("--val-split", default="val")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-iter", type=int, default=200)
    ap.add_argument("--n-restarts", type=int, default=5,
                    help="Independent EM inits per state count; the best "
                         "training log-likelihood wins. EM local optima are "
                         "large enough on real data to reorder a K-sweep.")
    ap.add_argument("--out", type=Path, required=True,
                    help="Where to write the fitted model + representations.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    _, train_seqs, vocab = load_phase_sequences(args.label_json, args.train_split)
    if not train_seqs:
        raise SystemExit(f"No videos in split {args.train_split!r}")
    n_obs = len(vocab)
    val_ids, val_seqs, _ = load_phase_sequences(args.label_json, args.val_split)
    logger.info("Loaded %d train / %d val videos, %d phase labels",
                len(train_seqs), len(val_seqs), n_obs)

    if args.sweep is not None:
        candidates = args.sweep or [2, 3, 4, 6, 8, 10]
        result = select_n_states(train_seqs, n_obs, candidates=candidates,
                                 val=val_seqs or None, seed=args.seed,
                                 n_iter=args.n_iter, n_restarts=args.n_restarts)
        for row in result["sweep"]:
            extra = (f"  val_loglik/frame {row['val_loglik_per_frame']:+.4f}"
                     if "val_loglik_per_frame" in row else "")
            logger.info("  K=%2d  BIC %14.1f  params %5d%s",
                        row["n_states"], row["bic"], row["n_free_params"], extra)
        logger.info("Best by BIC: K=%d", result["best_by_bic"])
        if "best_by_val_loglik" in result:
            logger.info("Best by held-out loglik: K=%d", result["best_by_val_loglik"])
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2))
        logger.info("Wrote %s", args.out)
        return

    model = fit_hmm(train_seqs, n_states=args.n_states, n_obs=n_obs,
                    seed=args.seed, n_iter=args.n_iter,
                    n_restarts=args.n_restarts)

    # Per-video representations for every split, both modes.
    all_ids, all_seqs, _ = load_phase_sequences(args.label_json, None)
    reps = {
        vid: {
            "causal": video_representation(model, obs, "causal").tolist(),
            "oracle": video_representation(model, obs, "oracle").tolist(),
        }
        for vid, obs in zip(all_ids, all_seqs)
    }

    causal_vecs = [np.asarray(r["causal"]) for r in reps.values()]
    oracle_vecs = [np.asarray(r["oracle"]) for r in reps.values()]
    payload = {
        "source_labels": str(args.label_json),
        "n_states": args.n_states,
        "seed": args.seed,
        "phase_vocab": vocab,
        "model": model.to_dict(),
        "representations": reps,
        "entropy_causal": representation_entropy(causal_vecs),
        "entropy_oracle": representation_entropy(oracle_vecs),
    }
    if val_seqs:
        payload["val_loglik_per_frame"] = (
            total_log_likelihood(model, val_seqs)
            / sum(s.shape[0] for s in val_seqs))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    logger.info("H(z) causal (normalized): %.3f | oracle: %.3f",
                payload["entropy_causal"]["hard_assignment_entropy_normalized"],
                payload["entropy_oracle"]["hard_assignment_entropy_normalized"])
    logger.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
