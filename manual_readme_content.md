This connector supports connecting to Git repositories using both **HTTP(S)** and **SSH**.

- **For HTTP(S):**

  - **Private repositories** require a username and password or an access token.
  - **Public repositories** do not require credentials for read operations (e.g., `pull`), but credentials are needed for write operations (e.g., `push`).
  - If credentials are provided but not required, they will be ignored.

- **For SSH:**

  - The username should be included in the URL ( **git** @gitrepo).
  - When SSH is used, the `username` and `password` fields are ignored.

The cloned repository is saved under:
`     ${PHANTOM_HOME_DIR}/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/<repo_name>    `

The **`repo_name`** parameter determines the name of the cloned folder.

## Authentication Methods

### 1. Basic Authentication (Username/Password)

To connect using basic authentication:

- Set the repository URL, for example:\
  `https://github.com/org/repo.git`
- Enter your credentials in the **Username** and **Password** fields.

### 2. Access Token Authentication

This connector now supports **Personal Access Tokens (PATs)** for secure authentication across platforms.\
Access tokens are preferred over username/password if both are provided.

To configure:

- Set the repository URL, for example:\
  `https://github.com/org/repo.git`
- Enter the token in the **Access token for the repository** field.

### How to Generate Access Tokens

- **GitHub**\
  Generate from: Settings → Developer settings → Personal access tokens → Tokens (classic)
  Generate a new token with required scopes (like repo, workflow, etc.)
  Docs: [GitHub PAT(classic) Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#personal-access-tokens-classic)

- **GitLab**\
  Generate from: Click on profile → Preferences → Access Tokens
  Docs: [GitLab PAT Documentation](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

- **Bitbucket**\
  Generate from: Go to your repo → Repository settings → Access tokens\
  Docs: [Bitbucket Access Tokens](https://support.atlassian.com/bitbucket-cloud/docs/access-tokens/)

### 3. Connecting via SSH

This app supports connecting to git through SSH instead of HTTP. In order to make this easy to do,
there is a **configure ssh** action. Running this action will create an RSA key pair, and return the
public key. After that, you will need to manually add the public key to the git repo.

Though not recommended, it is also possible to add an existing private key for this app to read, as
well. Add the private key file to

```
${PHANTOM_HOME_DIR}/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/.ssh-<asset_id>/id_rsa
```

Then set it so that

```
phantom-worker
```

is the owner, and set the file permissions to

```
600
```

If you do connect with SSH, both the username and password parameters will be ignored.

## Playbook Backward Compatibility

- The behavior of the clone repo and delete repo actions have been modified due to the change in
  the naming convention of repo.

  - In previous version, repo was saved as **reponame** In the new version, repo will be saved
    as **\_**
