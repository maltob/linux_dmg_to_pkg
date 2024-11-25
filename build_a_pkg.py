import subprocess
import os
import pathlib
import shutil
import plistlib
from string import Template
import tempfile


class MacOSAppInfo:
    CFBundleIdentifier: str
    CFBundleVersion: str
    CFBundleName: str
    CFBundleExecutable: str
    CFBundleDisplayName: str
    LSMinimumSystemVersion: str

    def load_from_info_plist(self,path: str):
        with open(path, 'rb') as iplfd:
            plist = plistlib.load(iplfd)
            if 'CFBundleIdentifier' in plist:
                self.CFBundleIdentifier = plist["CFBundleIdentifier"]
            if 'CFBundleVersion' in plist:
                self.CFBundleVersion = plist["CFBundleVersion"]
            if 'CFBundleName' in plist:
                self.CFBundleName = plist["CFBundleName"]
            if 'CFBundleExecutable' in plist:
                self.CFBundleExecutable = plist["CFBundleExecutable"]
            if 'CFBundleDisplayName' in plist:
                self.CFBundleDisplayName = plist["CFBundleDisplayName"]
            if 'LSMinimumSystemVersion' in plist:
                self.LSMinimumSystemVersion = plist["LSMinimumSystemVersion"]

def extract_dmg_app_and_contents(dmg_path: str, destination: str):
    with tempfile.TemporaryDirectory("dmg_") as tdir:
        convert_result = subprocess.run(['/usr/bin/7zzs', 'x', dmg_path,f"-o{tdir}"],shell=False)
        for app in pathlib.Path(tdir).glob("*/*.app"):
            shutil.copytree(app.absolute(),destination+"/"+app.name,dirs_exist_ok=True)
        for pkg in pathlib.Path(tdir).glob("*/*.pkg"):
            shutil.copyfile(pkg.absolute(),destination+"/"+pkg.name)
_input_path = "input"

#Check if we mapped a volume for working on
if not os.path.isdir(_input_path):
    exit(1)

#Has a dmg - we should mount it and pull the app out
for dmg in pathlib.Path(_input_path).glob("*.dmg"):
    dmg_path = dmg.absolute()
    extract_dmg_app_and_contents(dmg_path= dmg_path, destination=_input_path)    
    
has_app: bool = False
for app in pathlib.Path(_input_path).glob("*.app"):
    has_app = True

has_pkg: bool = False
for pkg in pathlib.Path(_input_path).glob("*.pkg"):
    shutil.copyfile(pkg.absolute(),f"/out/{pkg.name}")
    has_pkg = True

#If the DMG has a package - we can stop
if  has_pkg:
    exit(0)

if not has_app:
    print("No app to package!")
    exit(1)

#Package the app
#Root is where we create the payload from
#Flat is where we make the pkg from with root GZ'd into a Payload file
with tempfile.TemporaryDirectory("app_") as _package_base_path:
    pathlib.Path(f"{_package_base_path}/flat/Resources/en.lproj").mkdir(parents=True)
    pathlib.Path(f"{_package_base_path}/flat/base.pkg").mkdir(parents=True)
    pathlib.Path(f"{_package_base_path}/root/Applications").mkdir(parents=True)

    app_name = "ConvertedApp"
    appInfo = MacOSAppInfo()
    #Copy over all apps
    for app in pathlib.Path(_input_path).glob("*.app"):
        shutil.copytree(app.absolute(),f"{_package_base_path}/root/Applications/{app.name}")
        app_name = app.name
        appInfo.load_from_info_plist(f"{_package_base_path}/root/Applications/{app.name}/Contents/Info.plist")
        

    identifier = "com.converted."+app_name


    #Get file counts and size for MacOS to use for progress and estimation of the install size
    file_count = 0
    file_size = 0
    for item in pathlib.Path(f"{_package_base_path}/root/").rglob("*"):
        if item.is_file() :
            file_count+= 1
            file_size += item.stat().st_size

    #Add the metadata
    package_info_template_src = ''
    with open('templates/PackageInfo.template','r')  as pi_file:
        package_info_template_src = pi_file.read()

    package_info_template = Template(package_info_template_src)
    package_info = package_info_template.substitute(IDENTIFIER=appInfo.CFBundleIdentifier,CFBUNDLE_IDENTIFIER=appInfo.CFBundleIdentifier,INSTALL_KBYTES=int(round(file_size/1024,ndigits=0)),NUMBER_OF_FILES=file_count,CFBUNDLEVERSION=appInfo.CFBundleVersion,PKG_VERSION="1.0",INSTALL_LOCATION="/",APP_PATH=f"./Applications/{app_name}",MIN_OS_VERSION="11.0",APP_NAME=app_name)

    #Make a Distribution file https://developer.apple.com/library/archive/documentation/DeveloperTools/Reference/DistributionDefinitionRef/Chapters/Distribution_XML_Ref.html
    distribution_template_src = ''
    with open('templates/Distribution.template','r')  as di_file:
        distribution_template_src = di_file.read()
    distribution_template = Template(distribution_template_src)
    distribution = distribution_template.substitute(IDENTIFIER=appInfo.CFBundleIdentifier,CFBUNDLE_IDENTIFIER=appInfo.CFBundleIdentifier,INSTALL_KBYTES=int(round(file_size/1024,ndigits=0)),NUMBER_OF_FILES=file_count,CFBUNDLEVERSION=appInfo.CFBundleVersion,PKG_VERSION="1.0",INSTALL_LOCATION="/",APP_PATH=f"./Applications/{app_name}",MIN_OS_VERSION="11.0",APP_NAME=app_name)


    with open(f"{_package_base_path}/flat/base.pkg/PackageInfo", "w") as pkgInfoFd:
        pkgInfoFd.write(package_info)

        
    with open(f"{_package_base_path}/flat/Distribution", "w") as distFd:
        distFd.write(distribution)

    #Package it up to CPIO and GZIP
    subprocess.call(f"( cd {_package_base_path}/root && find . | cpio -o --format odc --owner 0:80 | gzip -c ) > {_package_base_path}/flat/base.pkg/Payload",shell=True)
    subprocess.call(f"mkbom -u 0 -g 80 {_package_base_path}/root {_package_base_path}/flat/base.pkg/Bom",shell=True)
    subprocess.call(f"cd {_package_base_path}/flat/ && xar --compression none -cf \"/out/{appInfo.CFBundleIdentifier}.pkg\" *",shell=True)
    subprocess.call(f"( cd {_package_base_path} && pwd )",shell=True)

