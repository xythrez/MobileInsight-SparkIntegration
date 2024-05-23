FROM apache/spark:3.5.1-scala2.12-java17-python3-r-ubuntu

ARG MAX_THREADS=1
ARG WS_VER=3.4.0
ARG MI_COMMIT=14184a0
ARG WIRESHARK_URL=https://github.com/wireshark/wireshark/archive/refs/tags/v${WS_VER}.tar.gz
ADD 00-cpp_compat.patch /build/00-cpp_compat.patch
ADD 01-radio_bearer_config.patch /build/01-radio_bearer_config.patch

USER root:root

# Run apt update
RUN set -ex; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y \
            git \
            cmake \
            bison \
            flex \
            python3-matplotlib \
            python3-pandas \
            libglib2.0-dev \
            libpcap-dev \
            libgcrypt-dev \
            libc-ares-dev; \
    pip3 install pyspark[sql]==3.5.1 dill==0.3.8;

# Download resources
RUN set -ex; \
    mkdir -p /build; \
    cd /build; \
    wget "$WIRESHARK_URL" -nv -O "wireshark-$WS_VER.tar.xz"; \
    tar -xf "wireshark-$WS_VER.tar.xz"; \
    git clone "https://github.com/xythrez/mobileinsight-core.git"; \
    git -C mobileinsight-core checkout "$MI_COMMIT";

# Compile and install wireshark
RUN set -ex; \
    cd "/build/wireshark-$WS_VER"; \
    for patch in /build/*.patch; do \
        patch -p1 < "$patch"; \
    done; \
    cmake -DBUILD_wireshark=OFF .; \
    make -j "$MAX_THREADS"; \
    make install; \
    ldconfig;

# Compile and install Wireshark dissector
Run set -ex; \
    cd /build/mobileinsight-core/ws_dissector; \
    g++ ws_dissector.cpp packet-aww.cpp -o ws_dissector \
        $(pkg-config --libs --cflags glib-2.0) \
        -I"/build/wireshark-$WS_VER" \
        -L"/usr/local/lib" \
        -lwireshark \
        -lwsutil \
        -lwiretap; \
    strip ws_dissector; \
    install -Dm 755 ws_dissector /usr/local/bin/ws_dissector;

# Compile and install MobileInsight
Run set -ex; \
    cd /build/mobileinsight-core; \
    pip3 install pyserial; \
    python3 setup.py install;

# Link python3 to python
Run set -ex; \
    cd /usr/bin; \
    ln -s python3 python;

# Cleanup
Run set -ex; \
    apt-get remove -y \
        git \
        cmake; \
    apt-get autoremove -y; \
    apt-get autoclean -y; \
    rm -rf /build;
