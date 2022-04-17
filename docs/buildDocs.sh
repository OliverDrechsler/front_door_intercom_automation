#!/bin/bash
set -x
apt-get update
apt-get -y install git rsync python3-sphinx python3-sphinx-rtd-theme
pwd
ls -lisah
export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
make clean html 
git config --global user.name "${GITHUB_ACTOR}"
git config --global user.email "${GITHUB_ACTOR}@users.noreply.github.com"
docroot=`mktemp -d`
rsync -av "docs/_build/html/" "${docroot}/" 
pushd "${docroot}"
git init
git remote add deploy "https://token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git checkout -b gh_pages
touch .nojekyll
 
# Add README
cat > README.md <<EOF
# GitHub Pages Cache
 
Nothing here only HitHub Pages

EOF

git add .
msg="Update Docs for commit ${GITHUB_SHA} made on `date -d"@${SOURCE_DATE_EPOCH}" --iso-8601=seconds` from ${GITHUB_REF} by ${GITHUB_ACTOR}"
git commit -am "${msg}"
git push deploy gh_pages --force 
popd
exit 0
