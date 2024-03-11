# File: git_connector.py
#
# Copyright (c) 2017-2024 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
#
#
# Standard library imports
import ast
import json
import os
import urllib.parse
from pathlib import Path
from shutil import rmtree

# Phantom imports
import phantom.app as phantom
import phantom.rules as phantom_rules
from Cryptodome.PublicKey import RSA
from phantom.action_result import ActionResult
from phantom.base_connector import BaseConnector

import git
# Local imports
import git_consts as consts


class GitConnector(BaseConnector):
    """ This is an AppConnector class that inherits the BaseConnector class. It implements various actions supported by
    git and helper methods required to run the actions.
    """

    def __init__(self):

        # Calling the BaseConnector's init function
        super(GitConnector, self).__init__()
        self.repo_uri = None
        self.repo_name = None
        self.branch_name = None
        self.username = None
        self.password = None
        self.app_state_dir = None
        self.modified_repo_uri = None
        self.ssh = False
        return

    def initialize(self):
        """ This is an optional function that can be implemented by the AppConnector derived class. Since the
        configuration dictionary is already validated by the time this function is called, it's a good place to do any
        extra initialization of any internal modules. This function MUST return a value of either phantom.APP_SUCCESS or
        phantom.APP_ERROR. If this function returns phantom.APP_ERROR, then AppConnector::handle_action will not get
        called.
        """

        self.config = self.get_config()
        self.app_state_dir = Path(self.get_state_dir())
        if self.get_action_identifier() == 'configure_ssh':
            return phantom.APP_SUCCESS
        self.username = self.config.get(consts.GIT_CONFIG_USERNAME)
        self.password = self.config.get(consts.GIT_CONFIG_PASSWORD)
        self.branch_name = self.config.get(consts.GIT_CONFIG_BRANCH_NAME, 'master')
        # Initializing to the value from config but setting again in _set_repo_attributes to allow access to param where user may have provided
        # a URL that should take precedent over any git URL configured in the app installation.
        self.repo_name = self.config.get(consts.GIT_CONFIG_REPO_NAME)
        self.repo_uri = self.config.get(consts.GIT_CONFIG_REPO_URI)

        http_proxy = os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('HTTPS_PROXY')
        if http_proxy:
            os.environ['http_proxy'] = http_proxy
        if https_proxy:
            os.environ['https_proxy'] = https_proxy

        return phantom.APP_SUCCESS

    def _set_repo_attributes(self, param={}):
        """
        Get some repo-specific attributes out of initialize for use in cloning without a configured asset
        """

        self.repo_uri = param.get('repo_url') or self.repo_uri
        self.branch_name = param.get('branch') or self.branch_name
        self.modified_repo_uri = self.repo_uri

        # create another copy so that URL with password is not displayed during test_connectivity action
        try:
            if self.repo_uri.startswith('http'):
                if self.username and self.password:
                    # encode password for any special character including @ and space
                    self.password = urllib.parse.quote_plus(self.password)
                    parse_result = urllib.parse.urlparse(self.repo_uri)
                    self.modified_repo_uri = '{scheme}://{username}:{password}@{netloc}{path}'.format(
                        scheme=parse_result[0], username=self.username, password=self.password, netloc=parse_result[1],
                        path=parse_result[2])
            else:
                self.save_progress('Connecting with SSH')
                self.ssh = True
                rsa_key_path = self.app_state_dir / '.ssh-{}'.format(self.get_asset_id()) / 'id_rsa'
                git_ssh_cmd = 'ssh -oStrictHostKeyChecking=no -i {}'.format(rsa_key_path)
                os.environ['GIT_SSH_COMMAND'] = git_ssh_cmd
        except AttributeError:
            return phantom.APP_ERROR

        # Parse the repo name from the repo uri
        try:
            self.modified_repo_uri = self.modified_repo_uri.rstrip('/')
            quoted_uri = urllib.parse.quote(self.modified_repo_uri, safe=":/?#[]@!$&\'()*,;=")
            temp_repo_name = quoted_uri.rsplit('/', 1)[1]

            # remove .git from the end
            temp_repo_name = temp_repo_name[:-4] if temp_repo_name.endswith('.git') else temp_repo_name
            self.repo_name = self.repo_name or f'{temp_repo_name}_{self.branch_name}'
        except Exception:
            return phantom.APP_ERROR

        return phantom.APP_SUCCESS

    def _list_repos(self, param):
        """ Function lists the git repos configured/pulled.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        summary_data = action_result.update_summary({})

        repo_list = set()
        repo_dirs = []

        # Iterate over each sub-directory in the app_state_dir to check for git repos
        subdirectories = [p for p in self.app_state_dir.iterdir() if p.is_dir()]
        self.debug_print('Iterating through subdirectories')
        for path in subdirectories:
            try:
                # returns absolute path if it is a git repo otherwise throws an exception
                repo_dir = Path(git.Repo(path).git_dir).parent

                if repo_dir.name not in repo_list:
                    repo_list.add(repo_dir.name)
                    repo_dirs.append(str(repo_dir))
            except git.exc.InvalidGitRepositoryError:
                continue

        appid = self.get_app_id()
        if appid in repo_list:
            repo_list.remove(appid)
        for repo_dir in repo_dirs:
            if repo_dir.endswith(appid):
                repo_dirs.remove(repo_dir)
                break

        action_result.add_data({'repos': list(repo_list), 'repo_dirs': repo_dirs})

        summary_data['total_repos'] = len(repo_list)
        self.debug_print('Total repositories: {}'.format(str(summary_data['total_repos'])))

        return action_result.set_status(phantom.APP_SUCCESS)

    def verify_repo(self, repo_name, action_result):
        """Function checks that directory for given repo exists and it is valid git repo.

        :param repo_name: Name of the repo to verify
        :param action_result: object of ActionResult class
        :return: status success/failure(along with appropriate message), repo object
        """

        try:
            repo_dir = self.app_state_dir / repo_name
        except Exception as e:
            self.debug_print(e)
            message = 'You must provide valid repo URI.'
            return action_result.set_status(phantom.APP_ERROR, message), repo_name

        try:
            repo = git.Repo(repo_dir)

        except git.exc.InvalidGitRepositoryError as e:
            self.debug_print(e)
            message = 'Directory is not a git repository: {}'.format(str(e))
            return action_result.set_status(phantom.APP_ERROR, message), repo_name

        except git.exc.NoSuchPathError as e:
            self.debug_print(e)
            message = 'Repository is not available: {}'.format(str(e))
            return action_result.set_status(phantom.APP_ERROR, message), repo_name

        except Exception as e:
            self.debug_print(e)
            message = 'Error while verifying the repo: {}'.format(str(e))
            return action_result.set_status(phantom.APP_ERROR, message), repo_name

        return phantom.APP_SUCCESS, repo

    def _file_interaction(self, action_result, action, file_path, contents='', vault_id=None):
        vault_file_data = None

        # verify that directory exists and it is valid git repo
        resp_status, repo = self.verify_repo(self.repo_name, action_result)
        if phantom.is_fail(resp_status):
            return action_result.get_status()

        repo_dir = self.app_state_dir / self.repo_name
        full_path = repo_dir / file_path
        try:
            if full_path.exists() and action == 'add':
                message = "File '{}' already exists in the local repository".format(file_path)
                return action_result.set_status(phantom.APP_ERROR, message)

            if not full_path.exists() and action in ['update', 'delete']:
                message = "File '{}' is not present in the local repository".format(file_path)
                return action_result.set_status(phantom.APP_ERROR, message)
        except IOError as ex:
            ex = str(ex)
            if 'File name too long' in ex:
                return action_result.set_status(phantom.APP_ERROR, 'File name too long')
            else:
                return action_result.set_status(phantom.APP_ERROR, ex)
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR, str(e))

        if action in ['update', 'add']:

            # checks if the path given is inside repository
            repo_dir_parts = repo_dir.resolve().parts
            full_path_parts = full_path.resolve().parts

            if full_path_parts[:len(repo_dir_parts)] != repo_dir_parts:
                message = 'Path outside git repository'
                return action_result.set_status(phantom.APP_ERROR, message)

            if vault_id:

                try:
                    status, message, vault_file_info = phantom_rules.vault_info(vault_id=vault_id, container_id=self.get_container_id())
                except Exception as e:
                    self.debug_print(f'Exception : {e}')
                    return action_result.set_status(phantom.APP_ERROR)

                if not status:
                    self.debug_print('Unable to get vault_info: {}'.format(message))
                    return action_result.set_status(phantom.APP_ERROR, 'Unable to get vault_info: {}'.format(message))

                try:
                    vault_file_path = Path(list(vault_file_info)[0].get('path'))
                    vault_file_data = vault_file_path.read_bytes()
                except Exception as e:
                    self.debug_print(f'Exception : {e}')
                    return action_result.set_status(phantom.APP_ERROR)

            file_data = vault_file_data if vault_file_data else contents
            # try to unescape escaped strings, if it can
            try:
                file_data = ast.literal_eval('"{}"'.format(file_data))
                file_data = file_data.encode()
            except Exception:
                pass

            # create any missing parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # overwrite file into local disk
            full_path.write_bytes(file_data)

            # add into index
            repo.index.add(file_path)

        if action == 'delete':
            try:
                full_path.unlink()
            except Exception as e:
                message = 'Unable to delete file: {}'.format(str(e))
                return action_result.set_status(phantom.APP_ERROR, status_message=message)

            try:
                repo.index.remove(file_path)
            except Exception as e:
                message = 'Error while deleting the file from local repository: {}'.format(str(e))
                if 'did not match any files' in str(e):
                    message = "File '{}' does not exists in the local repository".format(file_path)
                return action_result.set_status(phantom.APP_ERROR, status_message=message)

        action_result.add_data({'repo_name': self.repo_name, 'repo_dir': str(repo_dir), 'file_path': file_path})

        message = "File '{}' {}ed successfully".format(file_path, action.rstrip('e'))

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _update_file(self, param):
        """ Function updates the file content in local repository and updates the index.

        :param param: dictionary on input parameters
        :return: status success/failure
        """
        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)

        # get action parameters
        file_path = param['file_path'].strip().strip('/')
        contents = param.get('contents', '')
        vault_id = param.get('vault_id')

        return self._file_interaction(action_result, 'update', file_path, contents, vault_id)

    def _delete_file(self, param):
        """ Function deletes the file in local repository and deletes file from index.

        :param param: dictionary on input parameters
        :return: status success/failure
        """
        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)

        # get action parameters
        file_path = param['file_path'].strip().strip('/')

        return self._file_interaction(action_result, 'delete', file_path)

    def _add_file(self, param):
        """ Function adds the file in local repository and adds the file into index.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)

        # get action parameters
        file_path = param['file_path'].strip().strip('/')
        contents = param.get('contents', '')
        vault_id = param.get('vault_id')

        return self._file_interaction(action_result, 'add', file_path, contents, vault_id)

    def push(self, repo, action_result):
        """Push git local git repo into remote repository.

        :param repo: Repo name to push
        :param action_result: object of class ActionResult
        :return: status success/failure
        """

        try:
            repo.git.push()
        except Exception as e:
            self.debug_print(e)
            message = 'Error while pushing the repository to remote server: {}'.format(str(e))

            if 'You may want to first integrate the remote changes' in str(e):
                message = 'Latest changes are not available in local repo. You may want to do a ' \
                          'git pull first before pushing again.'

            if 'Invalid username or password' in str(e):
                message = 'Authentication failed'

            return action_result.set_status(phantom.APP_ERROR, status_message=message)

        return phantom.APP_SUCCESS

    def _git_commit(self, param):
        """ Function commits the repo.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)
        commit_message = param['message']
        push = param['push']

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        # config global user for commit
        with repo.config_writer() as writer:
            writer.set_value('user', 'name', self.username if self.username else 'default')
            writer.set_value('user', 'email', self.username if self.username else 'default')

        try:
            repo.git.commit(m=commit_message)
        except Exception as e:
            message = 'Error while committing the repo: {}'.format(str(e))
            self.debug_print(e)

            if 'nothing to commit' in str(e):
                message = 'Nothing to commit, working directory clean.'

            return action_result.set_status(phantom.APP_ERROR, message)

        if str(push).lower() == 'true':
            response = self.push(repo, action_result)

            if phantom.is_fail(response):
                return action_result.get_status()

        repo_dir = self.app_state_dir / self.repo_name
        message = 'Commit to repo {} completed successfully'.format(self.repo_name)
        action_result.add_data({
            'repo_name': self.repo_name,
            'repo_dir': str(repo_dir),
            'branch_name': self.branch_name,
            'commit_message': commit_message
        })

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _git_push(self, param):
        """ Function pushes local repository into remote repository.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)
        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        response = self.push(repo, action_result)

        if phantom.is_fail(response):
            return action_result.get_status()

        repo_dir = self.app_state_dir / self.repo_name
        message = 'Repo {} pushed successfully'.format(self.repo_name)
        action_result.add_data({'repo_name': self.repo_name, 'repo_dir': str(repo_dir), 'branch_name': self.branch_name})

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _git_pull(self, param):
        """ Function pulls repository.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)

        # if http(s) URI and username or password is not provided
        if not self.ssh and not (self.username and self.password):
            message = consts.GIT_USERNAME_AND_PASSWORD_REQUIRED
            self.debug_print(message)
            return action_result.set_status(phantom.APP_ERROR, status_message=message)

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        try:
            response = repo.git.pull()
            self.debug_print(response)
        except Exception as e:
            message = 'Error while pulling the repository: {}'.format(str(e))
            self.debug_print(e)

            if 'You have not concluded your merge' in str(e):
                message = 'Please, commit your changes before you can merge.'

            if 'Pull is not possible because you have unmerged files' in str(e):
                message = 'Pull is not possible because you have unmerged files. Fix them and make a commit.'

            return action_result.set_status(phantom.APP_ERROR, message)

        repo_dir = self.app_state_dir / self.repo_name
        message = 'Repo {} pulled successfully'.format(self.repo_name)
        action_result.add_data({'response': response, 'repo_name': self.repo_name, 'repo_dir': str(repo_dir), 'branch_name': self.branch_name})

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _delete_clone(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        repo_url = param.get('repo_url')
        if not repo_url and not self.repo_name and not self.repo_uri:
            message = consts.GIT_URL_OR_CONFIG_REQUIRED
            self.debug_print(message)
            return action_result.set_status(phantom.APP_ERROR, message)

        self._set_repo_attributes(param=param)
        self.modified_repo_uri = repo_url or self.modified_repo_uri
        self.branch_name = param.get('branch', self.branch_name)

        try:
            repo_dir = self.app_state_dir / self.repo_name
        except Exception as e:
            self.debug_print(e)
            message = 'You must provide valid repo URI.'
            return action_result.set_status(phantom.APP_ERROR, message)

        try:
            if not repo_dir.is_dir():
                msg = '{} could not be found'.format(self.repo_name)
                self.debug_print(msg)
                return action_result.set_status(
                    phantom.APP_ERROR, msg
                )
        except Exception as e:
            msg = 'Error: {}'.format(str(e))
            self.debug_print(msg)
            return action_result.set_status(
                phantom.APP_ERROR, msg
            )

        git_dir = repo_dir / '.git'
        if not git_dir.is_dir():
            msg = "{} doesn't appear to be a git repository".format(self.repo_name)
            self.debug_print(msg)
            return action_result.set_status(
                phantom.APP_ERROR, msg
            )

        try:
            rmtree(repo_dir, ignore_errors=True)
        except Exception as e:
            msg = 'Error deleting repository: {}'.format(str(e))
            self.debug_print(msg)
            return action_result.set_status(
                phantom.APP_ERROR, msg
            )

        # Track errors:
        files_not_deleted = [str(f.relative_to(repo_dir)) for f in repo_dir.glob('**/*')]
        if files_not_deleted:
            message = 'Some files could not be deleted in the repo. Check permissions of the files before trying again.'
        else:
            message = 'Successfully deleted repository'

        action_result.add_data({'repo_dir': str(repo_dir), 'unable_to_delete': files_not_deleted})

        return action_result.set_status(phantom.APP_SUCCESS, message)

    def _clone_repo(self, param):
        """ Function clones remote repository into local repository.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        repo_url = param.get('repo_url')
        if not self.config.get('repo_uri') and not repo_url:
            message = consts.GIT_URL_OR_CONFIG_REQUIRED
            self.debug_print(message)
            return action_result.set_status(phantom.APP_ERROR, message)

        self._set_repo_attributes(param=param)
        try:
            repo_dir = self.app_state_dir / self.repo_name
        except Exception as e:
            self.debug_print(e)
            message = 'You must provide valid repo URI.'
            return action_result.set_status(phantom.APP_ERROR, message)

        try:
            git.Repo.clone_from(self.modified_repo_uri, to_path=repo_dir,
                                branch=self.branch_name)

            message = 'Repo {} cloned successfully'.format(self.repo_name)
        except Exception as e:
            self.debug_print(e)
            e = str(e)
            if self.password:
                e = e.replace(self.password, '***')
            message = 'Error while cloning the repository: {}'.format(str(e))

            # when repo URI is wrong and username and password are valid
            if 'Repository not found' in str(e):
                message = 'Repo not found'

            if 'branch {} not found'.format(self.branch_name) in str(e):
                message = 'Branch name is invalid/incorrect'

            # when repo URI is wrong and username or password is not configured or is invalid
            if 'username' in str(e):
                message = 'Invalid username or password. Please make sure that you have correct access rights and' \
                          'repository exists'

            if 'Permission denied' in str(e):
                message = 'Permission denied. Please make sure that you have correct access rights'

            if 'already exists' in str(e):
                message = 'Repo already exists'

            return action_result.set_status(phantom.APP_ERROR, message)

        response = {'repo_name': self.repo_name, 'repo_dir': str(repo_dir), 'branch_name': self.branch_name}
        action_result.add_data(response)

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _configure_ssh(self, param):
        """ This function will create an RSA Key pair.

        :param param: dictionary of input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        force_new = param['force_new']

        ssh_key_dir = self.app_state_dir / '.ssh-{}'.format(self.get_asset_id())
        rsa_key_path = ssh_key_dir / 'id_rsa'
        rsa_pub_key_path = ssh_key_dir / 'id_rsa.pub'

        if rsa_key_path.is_file():
            if str(force_new).lower() == 'true':
                self.debug_print('Deleting old RSA key pair')
                try:
                    rsa_key_path.unlink()
                    rsa_pub_key_path.unlink()
                except Exception:
                    self.debug_print('Something went wrong while deleting old RSA key pair')
            else:
                try:
                    summary = action_result.update_summary({})
                    summary['rsa_pub_key'] = rsa_pub_key_path.read_bytes()
                except Exception:
                    pass
                return action_result.set_status(phantom.APP_ERROR, 'RSA Key already exists')

        key = RSA.generate(2048)

        ssh_key_dir.mkdir(exist_ok=True)

        rsa_key_path.write_bytes(key.exportKey('PEM'))
        rsa_key_path.chmod(0o700)

        pub_key = key.publickey().exportKey('OpenSSH')
        rsa_pub_key_path.write_bytes(pub_key)

        summary = action_result.update_summary({})
        summary['rsa_pub_key'] = pub_key

        # Create temp pub_key to add to the vault
        pub_key_vault_path = ssh_key_dir / 'id_rsa.pub_vault'
        pub_key_vault_path.write_bytes(pub_key)
        status, message, vault_id = phantom_rules.vault_add(container=self.get_container_id(),
                                                            file_location=str(pub_key_vault_path),
                                                            file_name='id_rsa.pub')
        if not status:
            return action_result.set_status(phantom.APP_ERROR,
                                            'Error adding file to vault: {}'.format(message))

        return action_result.set_status(phantom.APP_SUCCESS, 'Rsa pub key: {}'.format(pub_key.decode()))

    def _git_status(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        self._set_repo_attributes(param=param)
        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        git = repo.git

        try:
            status_str = git.status()
            status_porcelain = git.status('--porcelain')
        except Exception as e:
            message = 'Error in git status: {}'.format(str(e))
            return action_result.set_status(phantom.APP_ERROR, message)

        val_map = {
            'M': 'modified',
            'R': 'renamed',
            'D': 'deleted',
            'A': 'new_file'
        }

        status_lines = status_porcelain.splitlines()
        staged = {}
        unstaged = {}
        untracked_list = []
        try:
            for line in status_lines:
                status_staged = line[0]
                status_unstaged = line[1]
                fname = line[3:]
                if status_staged == '?' and status_unstaged == '?':
                    untracked_list.append(fname)
                    continue
                if status_staged != ' ':
                    val = val_map.get(status_staged, status_staged)
                    if val in staged:
                        staged[val].append(fname)
                    else:
                        staged[val] = [fname]
                if status_unstaged != ' ':
                    val = val_map.get(status_unstaged, status_unstaged)
                    if val in unstaged:
                        unstaged[val].append(fname)
                    else:
                        unstaged[val] = [fname]
        except Exception as e:
            self.debug_print('Exception in parsing git status: {}'.format(str(e)))
            staged = {}
            unstaged = {}
            untracked_list = []

        try:
            action_result.update_summary({'status': status_str.splitlines()[1]})
        except Exception as e:
            self.debug_print('Error getting commits ahead: {}'.format(str(e)))

        status = {
            'output': status_str,
            'staged': staged,
            'unstaged': unstaged,
            'untracked_files': untracked_list,
            'repo_dir': str(self.app_state_dir / self.repo_name)
        }

        action_result.add_data(status)
        return action_result.set_status(phantom.APP_SUCCESS)

    def _test_asset_connectivity(self, param):
        """ This function tests the connectivity of an asset with given credentials.

        :param param: (not used in this method)
        :return: status success/failure
        """

        action_result = ActionResult()
        self._set_repo_attributes(param=param)
        self.save_progress(consts.GIT_CONNECTION_TEST_MSG)
        self.save_progress('Configured repo URI: {}'.format(self.repo_uri))

        remote_refs = []
        g = git.cmd.Git()

        # ls_remote function call the git command ls-remote
        try:
            repo_details = g.ls_remote(self.modified_repo_uri).split('\n')
        except Exception:
            if not self.repo_uri:
                self.save_progress(
                    "You haven't added a repo URI to test connectivity to.  Only 'clone repo' with a provided repo URL will work!"
                )
            else:
                self.save_progress('Error while calling configured URI')
            if self.ssh:
                self.save_progress('Do you still need to run the configure_ssh action?')
            self.set_status(phantom.APP_ERROR, consts.GIT_TEST_CONNECTIVITY_FAIL)
            return action_result.get_status()

        # create a list of refs
        for ref in repo_details:
            # if repo is empty
            if ref:
                remote_refs.append(ref.split('\t')[1])

        # if branch name is not in ref_list it is invalid
        for ref in remote_refs:
            if self.branch_name == ref.split('/')[-1]:
                break
        else:
            self.save_progress('Invalid branch name')
            self.set_status(phantom.APP_ERROR, consts.GIT_TEST_CONNECTIVITY_FAIL)
            return action_result.get_status()

        self.set_status_save_progress(phantom.APP_SUCCESS, consts.GIT_TEST_CONNECTIVITY_SUCCESS)
        return action_result.get_status()

    def handle_action(self, param):
        """ This function gets current action identifier and calls member function of its own to handle the action.

        :param param: dictionary which contains information about the actions to be executed
        :return: status success/failure
        """

        # Dictionary mapping each action with its corresponding actions
        action_mapping = {
            'clone_repo': self._clone_repo,
            'delete_clone': self._delete_clone,
            'delete_file': self._delete_file,
            'git_pull': self._git_pull,
            'add_file': self._add_file,
            'git_push': self._git_push,
            'list_repos': self._list_repos,
            'git_commit': self._git_commit,
            'update_file': self._update_file,
            'configure_ssh': self._configure_ssh,
            'git_status': self._git_status,
            'test_asset_connectivity': self._test_asset_connectivity
        }

        action = self.get_action_identifier()
        action_execution_status = phantom.APP_SUCCESS

        if action in action_mapping:
            action_function = action_mapping[action]
            action_execution_status = action_function(param)

        return action_execution_status

    def finalize(self):
        """ This function gets called once all the param dictionary elements are looped over and no more handle_action
        calls are left to be made. It gives the AppConnector a chance to loop through all the results that were
        accumulated by multiple handle_action function calls and create any summary if required. Another usage is
        cleanup, disconnect from remote devices etc.
        """

        return phantom.APP_SUCCESS


if __name__ == '__main__':

    import sys

    import pudb

    pudb.set_trace()
    if len(sys.argv) < 2:
        print('No test json specified as input')
        sys.exit(1)
    json_path = Path(sys.argv[1]).read_text()
    in_json = json.loads(json_path)
    print(json.dumps(in_json, indent=4))
    connector = GitConnector()
    connector.print_progress_message = True
    return_value = connector._handle_action(json.dumps(in_json), None)
    print(json.dumps(json.loads(return_value), indent=4))
    sys.exit(0)
