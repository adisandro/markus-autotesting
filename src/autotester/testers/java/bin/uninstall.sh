#!/usr/bin/env bash

remove_tester() {
    echo "[JAVA-UNINSTALL] Removing compiled tester"
    rm -rf "${JAVADIR}/build"
    rm -rf "${JAVADIR}/.gradle"
}

reset_specs() {
    echo "[JAVA-UNINSTALL] Resetting specs"
    rm -f "${SPECSDIR}/install_settings.json"
}

# script starts here
if [[ $# -ne 0 ]]; then
    echo "Usage: $0"
    exit 1
fi

# vars
THISSCRIPT=$(readlink -f "${BASH_SOURCE[0]}")
THISDIR=$(dirname "${THISSCRIPT}")
SPECSDIR=$(readlink -f "${THISDIR}/../specs")
JAVADIR=$(readlink -f "${THISDIR}/../lib")

# main
remove_tester
reset_specs
echo "[JAVA-UNINSTALL] The following system packages have not been uninstalled: python3 openjdk-12-jdk jq. You may uninstall them if you wish."
rm -f "${SPECSDIR}/.installed"
