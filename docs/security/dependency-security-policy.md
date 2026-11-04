# Dependency security: mandatory before install or first execution

The user requires a security check BEFORE installing or upgrading anything, including transitive dependencies, one-shot executors (npx/uvx/pipx), plugins, downloaded tools, container images, and framework-managed automatic installs. Ordinary task authorization does not waive this requirement.

- Resolve exact versions and the full dependency graph first, using metadata/download-only operations with lifecycle scripts and source builds disabled. Do not import or run newly downloaded code to inspect it.
- Check fresh vulnerability advisories for every resolved component and the container base OS where applicable. Use existing maintained tools/APIs (OSV, npm audit, Docker Scout or equivalent). Check vendor security notices and recent publisher/supply-chain incidents too; a clean CVE scan does not establish absence of malware.
- Verify the source/publisher and artifact hashes; verify signatures/provenance where available. Review installation hooks, Python .pth files, and other automatic execution paths. A registry-matching hash does not prove the publisher was uncompromised.
- Block installation/execution on any known vulnerability (including unscored findings), compromised release, integrity mismatch, failed/incomplete scan, or unresolved required security evidence. Prefer patched versions, fewer dependencies, or another tool. Do not silently accept findings or infer a security exception from a generic task request.
- Record a dated pre-install receipt with the exact versions, hashes/digests, tools and sources checked, findings, and remaining uncertainty. Install only those reviewed artifacts; changing the resolved graph invalidates the receipt. Recheck at installation time and after updates. Never install a scanner without applying these same checks to it first.
- Disable lifecycle scripts by default. Use isolated environments, least privilege, no credentials/host mounts, and restricted networking where practical. Isolation supplements the pre-install checks; it does not replace them.

These are standing instructions for the agent, not an operating-system block on other programs. Never claim that zero known findings guarantees vulnerability-free or attack-free software.
