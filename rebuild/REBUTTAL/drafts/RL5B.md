Thank you. The comparison you asked for is now in the paper, and it explains the gap more cleanly than our original text did.

**Absolute scores below RISE and supervised SINet-v2.** That's right, and a new anchor table [App. G] puts every number beside its backbone and its label usage:
- **Our arms, same code (SINet, ResNet-50, COD10K S_α):** C10 0.7175 and random 0.7151 (eight-seed means, seed-expansion campaign); mean teacher 0.6988 (three seeds, positive-control campaign).
- **S2R-COD as published, same backbone and protocol:** 0.7136 for its method and 0.6984 for mean teacher. Our arms sit at or slightly above the protocol's own published result, and our mean teacher reproduces theirs to within 0.0004.
- **Methods outside the protocol:** RISE uses a DINOv2 ViT-L/14 feature extractor and reaches 0.763 (0.790 with SAM), unsupervised. Supervised SINet trains on real masks and reaches 0.771.
- [WS4, pending: the same code trained on the same 4,040 real images with their real masks, three seeds per architecture, gives SINet … and SINet-v2 …. This is a descriptive anchor, committed before its runs with no decision rule.]

The absolute level is inherited from the protocol and the backbone: synthetic supervision on a ResNet-family detector. Our null concerns a narrower layer inside that protocol, which 1,000 synthetic images to add, and every arm we compare shares the same ceiling.

**Concentration changes the training set, but does it explain accuracy?** It does not, as far as we can measure, and we have split the claim accordingly [abstract, §3.2]. You were also right to discount the boundary result: re-scored at eight seeds, the SINet effect drops from 1.37× to 0.30× its bar, and we withdraw it.

**Scope.** A new paragraph [§4] bounds every claim to LAKE-RED's background-only variation, a fixed foreground pool, the S2R-COD protocol, and SINet/SINet-v2. It names foreground-varying generators and modern backbones as untested.

**"No evidence of benefit" vs "no effect."** See the general comment and the new table [§3.1]: we rule out benefits above +0.0067 S_α on the primary cell, and the same-shape direction contrast is equivalent at ±0.005 while targeted-versus-random is not.
