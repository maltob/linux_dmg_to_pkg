FROM ubuntu:24.04 AS baseos
RUN apt update -y && apt install -y python3 curl xz-utils
FROM ubuntu:24.04 AS bombuilder
RUN apt update -y  && apt install -y git build-essential autoconf libxml2-dev libssl-dev zlib1g-dev
RUN git clone "https://github.com/maltob/bomutils.git" /tmp/bomutils
WORKDIR /tmp/bomutils
RUN make
RUN git clone "https://github.com/mackyle/xar.git" /tmp/xar
WORKDIR /tmp/xar/xar
RUN sed -i 's/OpenSSL_add_all_ciphers/OPENSSL_init_crypto/g' configure.ac && ./autogen.sh && make
FROM baseos AS add7z
RUN curl https://www.7-zip.org/a/7z2408-linux-x64.tar.xz -o 7z.tar.xz && tar -xf 7z.tar.xz 7zzs && cp 7zzs /usr/bin/7zzs && chmod +x /usr/bin/7zzs
FROM add7z AS app
COPY --from=bombuilder /tmp/bomutils/build/bin/mkbom /usr/bin/
COPY --from=bombuilder /tmp/bomutils/build/bin/lsbom /usr/bin/
COPY --from=bombuilder /tmp/bomutils/build/bin/dumpbom /usr/bin/
COPY --from=bombuilder /tmp/xar/xar/src/xar /usr/bin/
RUN mkdir /app
RUN mkdir /out
COPY build_a_pkg.py /app/build_a_pkg.py
WORKDIR /app/
VOLUME /out
VOLUME /app/input
CMD python /app/build_a_pkg.py