set -ex

git pull origin master
# bump version
docker run --rm -v "$PWD":/app treeder/bump patch
version=`cat VERSION`
echo "version: $version"

# tag it
git commit -a -m "version $version"
git tag -a "$version" -m "version $version"
#git push
#git push --tags