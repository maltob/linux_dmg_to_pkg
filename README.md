# Linux DMG to PKG

A set of scripts to convert DMG's to PKG on Linux without needing a MacOS host. The PKG format is better supported by MDM's for deployment such as "JAMF Pro".
It does so by creating a pkg based off the last .app name it sees in the DMG. It will copy all the apps from the DMG into the pkg and install them in /Applications. This doesn't currently support adding scripts to the package.

## Branches

This repository has branches to automatically package different OSS applications into pkg format that don't already have a pkg. This uses a download.sh script to download the DMG into a ./input directory for the packaging python script to use.
