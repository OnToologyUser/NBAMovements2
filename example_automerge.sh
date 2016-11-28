#!/bin/bash -e



export GIT_COMMITTER_EMAIL='travis@travis'
export GIT_COMMITTER_NAME='Travis CI'

printf 'Checking out master\n'

git checkout master || exit
printf 'Merging %s\n' "$TRAVIS_COMMIT"

git merge "$TRAVIS_COMMIT" || exit

printf 'Pushing to %s\n' "$TRAVIS_REPO_SLUG"
push_uri="https://$GH_TOKEN@github.com/$TRAVIS_REPO_SLUG"
git push "$push_uri" master >/dev/null 2>&1
git push "$push_uri" :"$TRAVIS_BRANCH" >/dev/null 2>&1
