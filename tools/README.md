# Verification maintenance

The September 21, 2026 update imports the previously completed ChatGPT execution
records for 35 articles in five languages. It does not represent a new local run
of every article. The five corrected examples were independently rerun locally
with Python 3.12.14, including source preservation and overwrite refusal.

The original imported records had September 22 timestamps even though the import
occurred September 21. Unconfirmed future timestamps were omitted from the
published environment labels; runtime/version information was retained. The
reference-existence article retains the limitation that the earlier execution
tested network failure handling, not successful external-reference validation.

Install `beautifulsoup4` and `Pillow` in a Python environment, then run:

```sh
python tools/verify_corrections.py
```

`apply_verification_patches.py` accepts a directory containing `vfix_A.json`,
`vfix_B.json` and the eight completed translation objects. These are archived
under `_src/verification-patches`. After importing, run
`python tools/finalize_verification.py` to apply the local editorial corrections.
The static HTML is the deployment source; `_src` keeps editable English content.

Deployment uses the existing GitHub `Unpack site.zip` workflow and GitHub Pages.
Package the full site, preserve CNAME, .nojekyll, Google verification, redirects,
analytics, downloads and all language folders. Never upload only a partial site
ZIP: the existing workflow replaces the deployed tree with the archive contents.
