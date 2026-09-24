# Scientific Concept Figure List

These figures are slide assets for explaining `body_main_short.tex`. They are not inserted into the NeurIPS submission by default.

1. **Clip protocol / centered-window caveat**
   - Figure: `fig_scientific01_clip_protocol_bbp12.png`
   - Purpose: shows the exact strict-prefix versus centered-window distinction on real BBP12 frames sampled every 5 seconds.
   - Scientific boundary: phase labels are visual annotations only; they are not inference inputs.

2. **Causal-at-inference soft workflow token**
   - Figure: `fig_scientific02_causal_inference_soft_token.png`
   - Purpose: follows the actual inference-time algorithm: pixels -> phase logits -> predicted prefix sequence -> TF-IDF/PCA/centroid posterior -> soft token -> RSD head.
   - Scientific boundary: no ground-truth phase labels, full-video phase sequence, or full-video cluster ID are used at inference.

3. **Offline workflow-cluster construction**
   - Figure: `fig_scientific03_offline_workflow_cluster.png`
   - Purpose: explains what the workflow token encodes: phase-order transition bigrams clustered in the fitted TF-IDF/PCA/k-means space.
   - Scientific boundary: oracle uses a hard full-video cluster; causal inference uses the same fitted transform on predicted prefix phases and returns a soft posterior.

4. **Oracle-dependency scope**
   - Figure: `fig_scientific04_oracle_dependency_scope.png`
   - Purpose: separates retrospective oracle, teacher-forced causal training, and pixel-only causal inference.
   - Scientific boundary: the submission closes the inference-time oracle dependency, not the privileged training-time dependency.

5. **Claim pattern and semantic control**
   - Figure: `fig_scientific05_results_scope_and_control.png`
   - Purpose: summarizes why the paper argues for variability-dependent workflow conditioning: MB140 strict gains, Cholec80 strict null, and shuffled-token control.
   - Scientific boundary: strict-protocol results support deployment-relevant claims; centered-window numbers are caveated.
