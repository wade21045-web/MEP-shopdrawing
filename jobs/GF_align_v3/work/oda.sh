#!/bin/sh
export QT_QPA_PLATFORM=xcb LD_LIBRARY_PATH=/workspace/GF_hvac/work/oda/usr/bin/ODAFileConverter_27.10.0.0:$LD_LIBRARY_PATH
xvfb-run -a /workspace/GF_hvac/work/oda/usr/bin/ODAFileConverter_27.10.0.0/ODAFileConverter "$@"
