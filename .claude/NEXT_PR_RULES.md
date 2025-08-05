# Next PR Rules for .claude Maintenance

## 5 Rules for Contributors

1. **Update anchors.json when adding/removing public APIs**
   - Add new anchor with SHA1(path+symbol+file_sha) when creating public classes/functions
   - Mark anchors as "tombstone" when removing symbols (don't delete)

2. **Add QA entry for every bug fix**
   - Create `.claude/qa/fix-<issue-or-commit>.yml` with problem/cause/fix
   - Link to relevant anchors if code was modified

3. **Update hotspots.txt monthly**
   - Run: `git log --format="" --name-only --since="6 months ago" | sort | uniq -c | sort -rn | head -20`
   - Replace contents of `.claude/metadata/hotspots.txt`

4. **Create delta file for releases**
   - On version tag, create `.claude/delta/<prev>_to_<curr>.diff`
   - Include API changes and migration notes

5. **Update components.yml for new modules**
   - Add entry when creating new directories under `src/tunacode/`
   - Update risk_level based on criticality (high/medium/low)
