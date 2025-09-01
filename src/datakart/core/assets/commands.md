# Dynamic Versioning with hatch-vcs

This project uses `hatch-vcs` for automatic versioning based on Git tags.

## Releasing a new version

1.  Ensure all changes are committed.
2.  Create a new Git tag for the release. The tag name should be the version number (e.g., `v1.24.0`).

    ```shell
    git tag v1.24.0
    ```

3.  Push the tag to the remote repository.

    ```shell
    git push origin v1.24.0
    ```

When you build the project, `hatch-vcs` will use this tag to set the version in the package and in `src/datakart/__init__.py`.

---

```shell
python3 -m pip install --upgrade pip build
python3 -m build

python3 -m pip install --upgrade twine
python3 -m twine upload dist/*
```
