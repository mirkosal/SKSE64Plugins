from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8-sig")
    if old not in text:
        raise RuntimeError(f"Expected source block not found in {path}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"Patched {path}")


# SKSE 2.3.1 checks a new extended flag to distinguish plugins rebuilt for
# Address Library format 5. Preserve the original 0x350-byte ABI and dedicate
# bit 1 of versionIndependenceEx to the new format flag.
replace_once(
    "Shared/Shared/Include/Shared/SKSE/PluginVersionData.h",
    "\t\tstd::uint32_t backwardCompatible16629                  : 1 { false }; // 304 (0, 0)\n"
    "\t\tstd::uint32_t reservedVersionIndependenceExtendedFlags : 31 { 0 };    // 304 (0, 1)\n",
    "\t\tstd::uint32_t backwardCompatible16629                  : 1 { false }; // 304 (0, 0)\n"
    "\t\tstd::uint32_t addressLibraryV5                         : 1 { false }; // 304 (0, 1)\n"
    "\t\tstd::uint32_t reservedVersionIndependenceExtendedFlags : 30 { 0 };    // 304 (0, 2)\n",
)

replace_once(
    "ActorLimitFix/ActorLimitFix/Source/ActorLimitFix.cpp",
    "\t.author          = \"meh321 and KernalsEgg\",\n"
    "\t.addressLibrary  = true,\n",
    "\t.author          = \"meh321 and KernalsEgg\",\n"
    "\t.addressLibraryV5 = true,\n"
    "\t.addressLibrary  = true,\n",
)

# Extend the custom Address Library reader used by this monorepo. Formats 1/2
# are sparse and packed; format 5 uses a fixed 64-byte executable-name field
# followed by a dense uint32 offset array indexed directly by Address Library ID.
replace_once(
    "Shared/Shared/Include/Shared/Relocation/AddressLibrary.h",
    "\t\tenum class Format : std::int32_t\n"
    "\t\t{\n"
    "\t\t\tkSpecialEdition     = 1,\n"
    "\t\t\tkAnniversaryEdition = 2\n"
    "\t\t};\n",
    "\t\tenum class Format : std::int32_t\n"
    "\t\t{\n"
    "\t\t\tkSpecialEdition       = 1,\n"
    "\t\t\tkAnniversaryEdition   = 2,\n"
    "\t\t\tkAnniversaryEditionV5 = 5\n"
    "\t\t};\n",
)

header_marker = (
    "\t\tinputFileStream.read(reinterpret_cast<char*>(std::addressof(this->format)), sizeof(std::int32_t));\n\n"
    "\t\tif (this->format != SKYRIM_RELOCATE(Format::kSpecialEdition, Format::kAnniversaryEdition))\n"
)

header_replacement = (
    "\t\tinputFileStream.read(reinterpret_cast<char*>(std::addressof(this->format)), sizeof(std::int32_t));\n\n"
    "#ifdef SKYRIM_ANNIVERSARY_EDITION\n"
    "\t\tif (this->format == Format::kAnniversaryEditionV5)\n"
    "\t\t{\n"
    "\t\t\tstd::uint32_t version[4]{};\n"
    "\t\t\tinputFileStream.read(reinterpret_cast<char*>(version), sizeof(version));\n\n"
    "\t\t\tthis->productVersion.major    = static_cast<std::int32_t>(version[0]);\n"
    "\t\t\tthis->productVersion.minor    = static_cast<std::int32_t>(version[1]);\n"
    "\t\t\tthis->productVersion.revision = static_cast<std::int32_t>(version[2]);\n"
    "\t\t\tthis->productVersion.build    = static_cast<std::int32_t>(version[3]);\n\n"
    "\t\t\tif (this->productVersion != productVersion)\n"
    "\t\t\t{\n"
    "\t\t\t\tUtility::InformationBox::Error(\n"
    "\t\t\t\t\t\"Unexpected product version encountered, {}.{}.{}.{}. Expected {}.{}.{}.{}.\",\n"
    "\t\t\t\t\tthis->productVersion.major,\n"
    "\t\t\t\t\tthis->productVersion.minor,\n"
    "\t\t\t\t\tthis->productVersion.revision,\n"
    "\t\t\t\t\tthis->productVersion.build,\n"
    "\t\t\t\t\tproductVersion.major,\n"
    "\t\t\t\t\tproductVersion.minor,\n"
    "\t\t\t\t\tproductVersion.revision,\n"
    "\t\t\t\t\tproductVersion.build);\n"
    "\t\t\t}\n\n"
    "\t\t\tchar fileName[64]{};\n"
    "\t\t\tinputFileStream.read(fileName, sizeof(fileName));\n"
    "\t\t\tconst auto fileNameEnd = std::find(std::begin(fileName), std::end(fileName), '\\0');\n"
    "\t\t\tthis->fileName.assign(std::begin(fileName), fileNameEnd);\n\n"
    "\t\t\tconst auto& executableFileName = Executable::GetSingleton().GetPath().filename();\n"
    "\t\t\tif (::_stricmp(this->fileName.c_str(), executableFileName.string().c_str()) != 0)\n"
    "\t\t\t{\n"
    "\t\t\t\tUtility::InformationBox::Error(\n"
    "\t\t\t\t\t\"Unexpected file name encountered, {}. Expected {}.\",\n"
    "\t\t\t\t\tthis->fileName,\n"
    "\t\t\t\t\texecutableFileName.string());\n"
    "\t\t\t}\n\n"
    "\t\t\tstd::int32_t dataFormat{};\n"
    "\t\t\tinputFileStream.read(reinterpret_cast<char*>(std::addressof(this->pointerSize)), sizeof(std::int32_t));\n"
    "\t\t\tinputFileStream.read(reinterpret_cast<char*>(std::addressof(dataFormat)), sizeof(std::int32_t));\n"
    "\t\t\tinputFileStream.read(reinterpret_cast<char*>(std::addressof(this->addressCount)), sizeof(std::int32_t));\n"
    "\t\t\treturn;\n"
    "\t\t}\n"
    "#endif\n\n"
    "\t\tif (this->format != SKYRIM_RELOCATE(Format::kSpecialEdition, Format::kAnniversaryEdition))\n"
)

replace_once(
    "Shared/Shared/Source/Shared/Relocation/AddressLibrary.cpp",
    header_marker,
    header_replacement,
)

read_marker = (
    "\tvoid AddressLibrary::Read(std::ifstream& inputFileStream, const Header& header)\n"
    "\t{\n"
    "\t\tstd::uint64_t identifier;\n"
)

read_replacement = (
    "\tvoid AddressLibrary::Read(std::ifstream& inputFileStream, const Header& header)\n"
    "\t{\n"
    "#ifdef SKYRIM_ANNIVERSARY_EDITION\n"
    "\t\tif (header.format == Format::kAnniversaryEditionV5)\n"
    "\t\t{\n"
    "\t\t\tstd::uint64_t identifier = 0;\n"
    "\t\t\tfor (auto& element : this->span_)\n"
    "\t\t\t{\n"
    "\t\t\t\tstd::uint32_t offset{};\n"
    "\t\t\t\tinputFileStream.read(reinterpret_cast<char*>(std::addressof(offset)), sizeof(offset));\n"
    "\t\t\t\telement.identifier = identifier++;\n"
    "\t\t\t\telement.offset = offset;\n"
    "\t\t\t}\n"
    "\t\t\treturn;\n"
    "\t\t}\n"
    "#endif\n\n"
    "\t\tstd::uint64_t identifier;\n"
)

replace_once(
    "Shared/Shared/Source/Shared/Relocation/AddressLibrary.cpp",
    read_marker,
    read_replacement,
)

print("ActorLimitFix Skyrim 1.7.104 compatibility patch applied successfully.")
