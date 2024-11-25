#assumes ubuntu:24.04

sudo apt update -y && sudo apt install -y python3 curl xz-utils git build-essential autoconf libxml2-dev libssl-dev zlib1g-dev
curl https://www.7-zip.org/a/7z2408-linux-x64.tar.xz -o 7z.tar.xz && tar -xf 7z.tar.xz 7zzs && sudo cp 7zzs /usr/bin/7zzs && sudo chmod +x /usr/bin/7zzs
git clone "https://github.com/maltob/bomutils.git" /tmp/bomutils
git clone "https://github.com/mackyle/xar.git" /tmp/xar
cd /tmp/bomutils/
make && sudo make install
cd /tmp/xar/xar
sed -i 's/OpenSSL_add_all_ciphers/OPENSSL_init_crypto/g' configure.ac && ./autogen.sh && make && sudo cp src/xar /usr/bin/xar && sudo chmod +x /usr/bin/xar
