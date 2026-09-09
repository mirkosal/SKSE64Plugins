from pathlib import Path
import runpy


# Reuse the validated monorepo-wide Address Library v5 compatibility patch that
# was used for ActorLimitFix. It updates the shared Address Library reader and
# SKSE PluginVersionData ABI flags while leaving unrelated runtime code intact.
runpy.run_path("ci/patch_actorlimitfix_1_7_104.py", run_name="__main__")


path = Path("ScrambledBugs/ScrambledBugs/Source/ScrambledBugs.cpp")
text = path.read_text(encoding="utf-8-sig")
old = (
    '\t.author          = "KernalsEgg",\n'
    '\t.addressLibrary  = true,\n'
)
new = (
    '\t.author          = "KernalsEgg",\n'
    '\t.addressLibraryV5 = true,\n'
    '\t.addressLibrary  = true,\n'
)

if old not in text:
    raise RuntimeError("Expected ScrambledBugs PluginVersionData block not found")

path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Patched ScrambledBugs/ScrambledBugs/Source/ScrambledBugs.cpp")
print("ScrambledBugs Skyrim 1.7.104 compatibility patch applied successfully.")
