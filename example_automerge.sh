#!/bin/bash -e

printf 'Name of the repo %s\n' "$TRAVIS_REPO_SLUG"
repo_temp=$(mktemp -d)
git clone "https://github.com/$TRAVIS_REPO_SLUG" "$repo_temp"

cd "$repo_temp"


export GIT_COMMITTER_EMAIL='travis@travis'
export GIT_COMMITTER_NAME='Travis CI'

printf 'Checking out master branch\n'

git checkout origin/master || exit
printf 'Merging %s\n' "$TRAVIS_COMMIT"

git merge "$TRAVIS_COMMIT" || exit

printf 'Pushing to %s\n' "$TRAVIS_REPO_SLUG"
push_uri="https://$GH_TOKEN@github.com/$TRAVIS_REPO_SLUG"
git push "$push_uri" master >/dev/null 2>&1
git push "$push_uri" :"$TRAVIS_BRANCH" >/dev/null 2>&1
