# Git

Publisher: Splunk <br>
Connector Version: 4.1.3 <br>
Product Vendor: Generic <br>
Product Name: Git <br>
Minimum Product Version: 6.3.0

This app integrates with git and supports common git actions

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

This connector supports **Access Tokens (including Personal Access Tokens (PATs))** for secure authentication across platforms.\
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

### Configuration variables

This table lists the configuration variables required to operate Git. These variables are specified when configuring a Git asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**repo_uri** | optional | string | Repo URI |
**branch_name** | optional | string | Branch Name (Default: master) |
**username** | optional | string | Username |
**password** | optional | password | Password |
**repo_name** | optional | string | Repo Name |
**access_token** | optional | password | Access token for the repository |

### Supported Actions

[test connectivity](#action-test-connectivity) - Validate credentials provided for connectivity <br>
[configure ssh](#action-configure-ssh) - Create an RSA Key pair for SSH connectivity <br>
[list repos](#action-list-repos) - List repos configured/pulled <br>
[update file](#action-update-file) - Update (overwrite) contents of a file in the working directory <br>
[git status](#action-git-status) - Get the result of git status <br>
[delete file](#action-delete-file) - Delete a file from the local working directory <br>
[add file](#action-add-file) - Create a file in the local working directory <br>
[git commit](#action-git-commit) - Commit changes <br>
[git push](#action-git-push) - Push commits to the remote server <br>
[git pull](#action-git-pull) - Pull the repo <br>
[delete repo](#action-delete-repo) - Delete a cloned repository <br>
[clone repo](#action-clone-repo) - Clone the repo <br>
[on poll](#action-on-poll) - Schedule regular cloning of a repository

## action: 'test connectivity'

Validate credentials provided for connectivity

Type: **test** <br>
Read only: **True**

#### Action Parameters

No parameters are required for this action

#### Action Output

No Output

## action: 'configure ssh'

Create an RSA Key pair for SSH connectivity

Type: **generic** <br>
Read only: **False**

This action will generate a new RSA key pair to enable connecting via SSH. It will return the public key, which you should add to the repo that you wish to connect to.

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**force_new** | optional | Force create a new key pair | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.force_new | boolean | | True False |
action_result.data | string | | |
action_result.summary.rsa_pub_key | string | | ssh-rsa <key> |
action_result.message | string | | Rsa pub key |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'list repos'

List repos configured/pulled

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.data.\*.repo_dirs | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repos | string | | test_repo |
action_result.summary.total_repos | numeric | | 2 |
action_result.message | string | | Total repos: 2 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'update file'

Update (overwrite) contents of a file in the working directory

Type: **generic** <br>
Read only: **False**

This action will overwrite the contents of the existing file with the specified input in the local working directory.<br>If <b>vault_id</b> is specified the contents are overwritten from the file in the vault, else from the data in the <b>contents</b> parameter. The <b>contents</b> parameter can only contain textual data.

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_path** | required | File path in repo to update | string | `file path` |
**contents** | optional | Contents (text) of the file | string | |
**vault_id** | optional | Vault ID | string | `vault id` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.contents | string | | Contents to write in the file |
action_result.parameter.file_path | string | `file path` | b |
action_result.parameter.vault_id | string | `vault id` | 75881c96a30cd1f07d596059388368836b6b1b74 |
action_result.data.\*.file_path | string | `file path` | b |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.summary | string | | |
action_result.message | string | | File file1 updated successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'git status'

Get the result of git status

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.staged.deleted | string | `file path` | deleted_file |
action_result.data.\*.staged.modified | string | `file path` | modified_file |
action_result.data.\*.staged.new_file | string | `file path` | new_file |
action_result.data.\*.staged.renamed | string | | old_file -> new_file |
action_result.data.\*.str | string | | On branch master Your branch is up-to-date with 'origin/master'. nothing to commit, working directory clean |
action_result.data.\*.unstaged.modified | string | `file path` | modified_file |
action_result.data.\*.untracked_files | string | `file path` | untracked_file |
action_result.summary.status | string | | Your branch is up-to-date with 'origin/master'. |
action_result.message | string | | Status: Your branch is up-to-date with 'origin/master'. |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'delete file'

Delete a file from the local working directory

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_path** | required | File path in repo to delete | string | `file path` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.file_path | string | `file path` | n1 |
action_result.data.\*.file_path | string | `file path` | n1 |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.summary | string | | |
action_result.message | string | | File file1 deleted successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'add file'

Create a file in the local working directory

Type: **generic** <br>
Read only: **False**

This action will create in the working directory a file with the specified input data.<br>If <b>vault_id</b> is specified the contents are picked from the file in the vault, else from the data in the <b>contents</b> parameter. The <b>contents</b> parameter can only contain textual data.

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_path** | required | File path in repo to add | string | `file path` |
**contents** | optional | Contents (text) of the file | string | |
**vault_id** | optional | Vault ID | string | `vault id` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.contents | string | | new content |
action_result.parameter.file_path | string | `file path` | n1 |
action_result.parameter.vault_id | string | `vault id` | 75881c96a30cd1f07d596059388368836b6b1b74 |
action_result.data.\*.file_path | string | `file path` | n1 |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.summary | string | | |
action_result.message | string | | File file1 added successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'git commit'

Commit changes

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**message** | required | Commit message (Default: committed from splunk soar) | string | |
**push** | optional | Push to remote after commit | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.message | string | | committed from phantom |
action_result.parameter.push | boolean | | True False |
action_result.data.\*.branch_name | string | | master |
action_result.data.\*.commit_message | string | | committed from phantom |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.summary | string | | |
action_result.message | string | | Commit to repo test_repo completed successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'git push'

Push commits to the remote server

Type: **generic** <br>
Read only: **False**

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.data.\*.branch_name | string | | master |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.summary | string | | |
action_result.message | string | | Repo test_repo pushed successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'git pull'

Pull the repo

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.data.\*.branch_name | string | | master |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.data.\*.response | string | | Already up-to-date. |
action_result.summary | string | | |
action_result.message | string | | Repo test_repo pulled successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'delete repo'

Delete a cloned repository

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**repo_url** | optional | Repository URL | string | `github repo` `gitlab repo` `bitbucket repo` `git repo` |
**branch** | optional | Branch | string | `github branch` `gitlab branch` `bitbucket branch` `git branch` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.repo_url | string | `github repo` `gitlab repo` `bitbucket repo` `git repo` | |
action_result.parameter.branch | string | `github branch` `gitlab branch` `bitbucket branch` `git branch` | |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.summary | string | | |
action_result.message | string | | Successfully deleted repository |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'clone repo'

Clone the repo

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**repo_url** | optional | Repository URL | string | `github repo` `gitlab repo` `bitbucket repo` `git repo` |
**branch** | optional | Branch | string | `github branch` `gitlab branch` `bitbucket branch` `git branch` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failed |
action_result.parameter.repo_url | string | `github repo` `gitlab repo` `bitbucket repo` `git repo` | |
action_result.parameter.branch | string | `github branch` `gitlab branch` `bitbucket branch` `git branch` | |
action_result.data.\*.branch_name | string | | master |
action_result.data.\*.repo_dir | string | `file path` | /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo |
action_result.data.\*.repo_name | string | | repo2 |
action_result.summary | string | | |
action_result.message | string | | Repo test_repo cloned successfully |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'on poll'

Schedule regular cloning of a repository

Type: **ingest** <br>
Read only: **False**

For regular cloning of a specified repository.

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**repo_url** | optional | Repository URL | string | `github repo` `gitlab repo` `bitbucket repo` `git repo` |
**branch** | optional | Branch | string | `github branch` `gitlab branch` `bitbucket branch` `git branch` |

#### Action Output

No Output

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2025 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
