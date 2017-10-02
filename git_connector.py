# --
# File: git_connector.py
#
# Copyright (c) Phantom Cyber Corporation, 2017
#
# This unpublished material is proprietary to Phantom Cyber.
# All rights reserved. The methods and
# techniques described herein are considered trade secrets
# and/or confidential. Reproduction or distribution, in whole
# or in part, is forbidden except by express written permission
# of Phantom Cyber Corporation.
#
# --

# Standard library imports
import json
import urlparse
import os
import git
import urllib
import shutil
from Crypto.PublicKey import RSA

# Phantom imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult
from phantom.vault import Vault

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

        if self.get_action_identifier() == "configure_ssh":
            return phantom.APP_SUCCESS

        http_proxy = os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('HTTPS_PROXY')
        if http_proxy:
            os.environ['http_proxy'] = http_proxy
        if https_proxy:
            os.environ['https_proxy'] = https_proxy

        # Get configuration dictionary
        config = self.get_config()
        self.repo_uri = config[consts.GIT_CONFIG_REPO_URI]

        temp_repo_name = self.repo_uri.rsplit('/', 1)[1]

        # remove .git from the end
        temp_repo_name = temp_repo_name[:-4] if temp_repo_name.endswith('.git') else temp_repo_name

        # if repo name is given use that as folder name
        self.repo_name = config.get(consts.GIT_CONFIG_REPO_NAME, temp_repo_name)
        self.branch_name = config[consts.GIT_CONFIG_BRANCH_NAME]
        self.username = config.get(consts.GIT_CONFIG_USERNAME)
        self.password = config.get(consts.GIT_CONFIG_PASSWORD)
        self.app_state_dir = self.get_state_dir()

        # create another copy so that URL with password is not displayed during test_connectivity action
        if self.repo_uri.startswith('http'):
            if self.username and self.password:
                # encode password for any special character inlcluding @ and space
                self.password = urllib.quote_plus(self.password)
                parse_result = urlparse.urlparse(self.repo_uri)
                self.modified_repo_uri = "{scheme}://{username}:{password}@{netloc}{path}".format(
                    scheme=parse_result[0], username=self.username, password=self.password, netloc=parse_result[1],
                    path=parse_result[2])
        else:
            self.save_progress("Connecting with SSH")
            self.ssh = True
            asset_id = self.get_asset_id()
            ssh_key_dir = '{}.ssh-{}'.format(self.app_state_dir, asset_id)
            rsa_key_path = '{}/id_rsa'.format(ssh_key_dir)
            git_ssh_cmd = 'ssh -oStrictHostKeyChecking=no -i {}'.format(rsa_key_path)
            os.environ['GIT_SSH_COMMAND'] = git_ssh_cmd
            self.modified_repo_uri = self.repo_uri

        # change working directory to app state dir
        os.chdir(self.app_state_dir)

        return phantom.APP_SUCCESS

    def _list_repos(self, param):
        """ Function lists the git repos configured/pulled.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        summary_data = action_result.update_summary({})

        # list of path in app state directory
        dirpaths = [item[0] for item in os.walk(self.app_state_dir)]

        repo_list = []

        for path in dirpaths:
            try:
                # returns absolute path if it is a git repo otherwise throws an exception
                temp = git.Repo(path).git_dir

                # remove path upto app_state-dir/app_id from starting and /.git from the end
                temp = temp[len(self.app_state_dir):-5]

                if temp not in repo_list:
                    repo_list.append(temp)
            except:
                continue

        action_result.add_data({'repos': repo_list})

        summary_data['total_repos'] = len(repo_list)

        return action_result.set_status(phantom.APP_SUCCESS)

    def verify_repo(self, repo_name, action_result):
        """Function checks that directory for given repo exists and it is valid git repo.

        :param repo_name: Name of the repo to verify
        :param action_result: object of ActionResult class
        :return: status success/failure(along with appropriate message), repo object
        """

        try:
            repo = git.Repo(repo_name)

        except git.exc.InvalidGitRepositoryError as e:
            self.debug_print(e)
            message = "Directory is not a git repository: {}".format(str(e))
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status(), None

        except git.exc.NoSuchPathError as e:
            self.debug_print(e)
            message = "Repository is not available: {}".format(str(e))
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status(), None

        except Exception as e:
            self.debug_print(e)
            message = "Error while verifying the repo: {}".format(str(e))
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status(), None

        return phantom.APP_SUCCESS, repo

    def _update_file(self, param):
        """ Function updates the file content in local repository and updates the index.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        # get action parameters
        file_path = param['file_path']
        contents = param.get('contents')
        vault_id = param.get('vault_id')
        vault_file_data = None

        # verify that directory exists and it is valid git repo
        resp_status, repo = self.verify_repo(self.repo_name, action_result)
        if phantom.is_fail(resp_status):
            return action_result.get_status()

        # handles '/' at the beginning, empty string between two '/' and
        # space at the starting of string
        temp = []
        for item in file_path.split('/'):
            if item.strip():
                temp.append(item.strip())

        full_path = '/'.join(temp)
        full_path = '{}/{}'.format(self.repo_name, full_path)
        file_dir = full_path.rsplit('/', 1)[0]
        file_name = full_path.rsplit('/', 1)[1]

        # if path does not exist
        if not os.path.exists(full_path):
            message = "File {} is not present in the local repository".format(full_path.split('/', 1)[1])
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        os.chdir(file_dir)

        # if current directory is not under git repository
        if not os.getcwd().startswith('{}{}'.format(self.app_state_dir, self.repo_name)):
            message = "File {} is not present in the local repository".format(full_path.split('/', 1)[1])
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        if vault_id:
            vault_file_path = Vault.get_file_path(vault_id)

            # if vault_id is invalid vault_file_path will be none
            if not vault_file_path:
                message = "Invalid parameter: vault id"
                self.debug_print(message)
                action_result.set_status(phantom.APP_ERROR, message)
                return action_result.get_status()

            with open(vault_file_path, 'r') as vault_file:
                vault_file_data = vault_file.read()

        file_data = vault_file_data if vault_file_data else contents
        if not file_data:
            file_data = ""

        # overwrite file into local disk
        with open(file_name, 'w') as repo_file:
            repo_file.write(file_data)

        # add into index
        repo.index.add(['{}/{}'.format(os.getcwd(), file_name)[len('{}{}/'.format(self.app_state_dir,
                                                                                  self.repo_name)):]])

        response = {'repo_name': self.repo_name, 'file_path': file_path}
        action_result.add_data(response)
        message = "File {} updated successfully".format(full_path.split('/', 1)[1])

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _delete_file(self, param):
        """ Function deletes the file in local repository and deletes file from index.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        file_path = param['file_path']

        # handles '/' at the beginning, empty string between two '/' and
        # space at the starting and ending of string
        temp = []
        for item in file_path.split('/'):
            if item.strip():
                temp.append(item.strip())

        full_path = '/'.join(temp)
        full_path = "{}/{}".format(self.repo_name, full_path)
        file_dir = full_path.rsplit('/', 1)[0]
        file_name = full_path.rsplit('/', 1)[1]

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        try:
            os.chdir(file_dir)
            if not os.getcwd().startswith('{}{}'.format(self.app_state_dir, self.repo_name)):
                raise Exception

        except Exception as e:
            self.debug_print(e)
            message = 'File {} does not exists in the local repository'.format(full_path.split('/', 1)[1])
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        # remove file from local machine
        file_deleted = False
        try:
            os.remove(file_name)
            file_deleted = True
        except:
            pass

        # remove file from index
        try:
            repo.index.remove(['{}/{}'.format(os.getcwd(), file_name)[len('{}{}/'.format(self.app_state_dir,
                                                                                         self.repo_name)):]])
        except Exception as e:
            # if file was deleted from local repository action is successful
            if file_deleted:
                pass

            message = "Error while deleting the file from local repository"
            if 'did not match any files' in str(e):
                message = 'File {} does not exists in the local repository'.format(full_path.split('/', 1)[1])
                self.debug_print(message)

            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        message = "File {} deleted successfully".format(full_path.split('/', 1)[1])
        response = {'file_path': file_path, 'repo_name': self.repo_name}
        action_result.add_data(response)

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _add_file(self, param):
        """ Function adds the file in local repository and adds the file into index.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        file_path = param['file_path']
        contents = param.get('contents')
        vault_id = param.get('vault_id')
        vault_file_data = None

        # handles '/' at the beginning, empty string between two '/' and
        # space at the starting and ending of string
        temp = []
        for item in file_path.split('/'):
            if item.strip():
                temp.append(item.strip())

        file_path = '/'.join(temp)

        if vault_id:
            vault_file_path = Vault.get_file_path(vault_id)

            # if vault_id is invalid vault_file_path will be none
            if not vault_file_path:
                message = "Invalid parameter: vault id"
                self.debug_print(message)
                action_result.set_status(phantom.APP_ERROR, message)
                return action_result.get_status()

            with open(vault_file_path, 'r') as vault_file:
                vault_file_data = vault_file.read()

        file_data = vault_file_data if vault_file_data else contents
        if not file_data:
            file_data = ""

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        try:
            # file_dir contains full path except file name
            # file_name contains only file name
            full_path = "{}/{}".format(self.repo_name, file_path)
            file_dir = full_path.rsplit('/', 1)[0]
            file_name = full_path.rsplit('/', 1)[1]

            # if path does not exist, create one
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                # repo.index.add([file_dir])
            os.chdir(file_dir)

            if not os.getcwd().startswith('{}{}'.format(self.app_state_dir, self.repo_name)):
                message = "Path outside git repository"
                action_result.set_status(phantom.APP_ERROR, message)
                return action_result.get_status()

            with open(file_name, 'w') as repo_file:
                repo_file.write(file_data)

        except Exception as e:
            self.debug_print(e)
            message = "Error while writing the file into local repository: {}".format(str(e))
            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        repo.index.add(['{}/{}'.format(os.getcwd(), file_name)[len('{}{}/'.format(self.app_state_dir,
                                                                                  self.repo_name)):]])

        response = {'repo_name': self.repo_name, 'file_path': file_path}
        action_result.add_data(response)
        message = "File {} added successfully".format(file_name)

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

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
            message = "Error while pushing the repository to remote server: {}".format(str(e))

            if "You may want to first integrate the remote changes" in str(e):
                message = "Latest changes are not available in local repo. You may want to do a " \
                          "git pull first before pushing again."

            if "Invalid username or password" in str(e):
                message = "Authentication failed"

            return action_result.set_status(phantom.APP_ERROR, status_message=message)

        return phantom.APP_SUCCESS

    def _git_commit(self, param):
        """ Function commits the repo.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        commit_message = param['message']
        push = param['push']

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        # config global user for commit
        writer = repo.config_writer()
        writer.set_value('user', 'name', self.username if self.username else 'default')
        writer.set_value('email', 'name', self.username if self.username else 'default')

        try:
            repo.git.commit(m=commit_message)
        except Exception as e:
            message = "Error while committing the repo: {}".format(str(e))
            self.debug_print(e)

            if "nothing to commit" in str(e):
                message = "Nothing to commit, working directory clean."

            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        if str(push).lower() == 'true':
            response = self.push(repo, action_result)

            if phantom.is_fail(response):
                return action_result.get_status()

        message = "Commit to repo {} completed successfully".format(self.repo_name)
        action_result.add_data({'repo_name': self.repo_name, 'branch_name': self.branch_name,
                                'commit_message': commit_message})

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _git_push(self, param):
        """ Function pushes local repository into remote repository.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        response = self.push(repo, action_result)

        if phantom.is_fail(response):
            return action_result.get_status()

        message = "Repo {} pushed successfully".format(self.repo_name)
        action_result.add_data({'repo_name': self.repo_name, 'branch_name': self.branch_name})

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _git_pull(self, param):
        """ Function pulls repository.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

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
            message = "Error while pulling the repository: {}".format(str(e))
            self.debug_print(e)

            if "You have not concluded your merge" in str(e):
                message = "Please, commit your changes before you can merge."

            if "Pull is not possible because you have unmerged files" in str(e):
                message = "Pull is not possible because you have unmerged files. Fix them and make a commit."

            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        message = "Repo {} pulled successfully".format(self.repo_name)
        action_result.add_data({'response': response, 'repo_name': self.repo_name, 'branch_name': self.branch_name})

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _delete_clone(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        if not os.path.isdir(self.repo_name):
            return action_result.set_status(
                phantom.APP_ERROR, "{} could not be found".format(self.repo_name)
            )

        if not os.path.isdir('{}/.git'.format(self.repo_name)):
            return action_result.set_status(
                phantom.APP_ERROR, "{} doesn't appear to be a git repository".format(self.repo_name)
            )

        try:
            shutil.rmtree(self.repo_name)
        except Exception as e:
            return action_result.set_status(
                phantom.APP_ERROR, "Error deleting repository: {}".format(str(e))
            )

        return action_result.set_status(phantom.APP_SUCCESS, "Successfully deleted repository")

    def _clone_repo(self, param):
        """ Function clones remote repository into local repository.

        :param param: dictionary on input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        # if http(s) URI and username or password is not provided
        if not self.ssh and not (self.username and self.password):
            message = consts.GIT_USERNAME_AND_PASSWORD_REQUIRED
            self.debug_print(message)
            return action_result.set_status(phantom.APP_ERROR, status_message=message)

        try:
            git.Repo.clone_from(self.modified_repo_uri, to_path=self.repo_name,
                                branch=self.branch_name)

            message = 'Repo {} cloned successfully'.format(self.repo_name)
        except Exception as e:
            self.debug_print(e)
            message = 'Error while cloning the repository: {}'.format(str(e))

            # when repo URI is wrong and username and password are valid
            if 'Repository not found' in str(e):
                message = "Repo not found"

            if 'branch {} not found'.format(self.branch_name) in str(e):
                message = "Branch name is invalid/incorrect"

            # when repo URI is wrong and username or password is not configured or is invalid
            if 'username' in str(e):
                message = "Invalid username or password. Please make sure that you have correct access rights and" \
                          "repository exists"

            if 'Permission denied' in str(e):
                message = "Permission denied. Please make sure that you have correct access rights"

            if 'already exists' in str(e):
                message = 'Repo already exists'

            action_result.set_status(phantom.APP_ERROR, message)
            return action_result.get_status()

        response = {'repo_name': self.repo_name, 'branch_name': self.branch_name}
        action_result.add_data(response)

        return action_result.set_status(phantom.APP_SUCCESS, status_message=message)

    def _configure_ssh(self, param):
        """ This function will create an RSA Key pair.

        :param param: dictionary of input parameters
        :return: status success/failure
        """

        action_result = self.add_action_result(ActionResult(dict(param)))

        force_new = param['force_new']

        state_dir = self.get_state_dir()
        asset_id = self.get_asset_id()

        ssh_key_dir = '{}.ssh-{}'.format(state_dir, asset_id)
        rsa_key_path = '{}/id_rsa'.format(ssh_key_dir)
        rsa_pub_key_path = '{}/id_rsa.pub'.format(ssh_key_dir)

        if os.path.exists(rsa_key_path):
            if str(force_new).lower() == 'true':
                self.debug_print("Deleting old RSA key pair")
                try:
                    os.remove(rsa_key_path)
                    os.remove(rsa_pub_key_path)
                except:
                    pass
            else:
                return action_result.set_status(phantom.APP_ERROR, "RSA Key already exists")

        key = RSA.generate(2048)

        if not os.path.exists(ssh_key_dir):
            os.makedirs(ssh_key_dir)

        with open(rsa_key_path, 'w') as f:
            os.chmod(rsa_key_path, 0700)
            f.write(key.exportKey('PEM'))
            f.close()

        with open(rsa_pub_key_path, 'w') as f:
            f.write(key.publickey().exportKey('OpenSSH'))
            f.close()

        summary = action_result.update_summary({})
        summary['rsa_pub_key'] = key.publickey().exportKey('OpenSSH')

        resp = Vault.add_attachment(rsa_pub_key_path, self.get_container_id(), 'id_rsa.pub')
        if resp['succeeded'] is False:
            return action_result.set_status(phantom.APP_ERROR,
                                            "Error adding file to vault: {}".format(resp['message']))

        return action_result.set_status(phantom.APP_SUCCESS)

    def _git_status(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        resp_status, repo = self.verify_repo(self.repo_name, action_result)

        if phantom.is_fail(resp_status):
            return action_result.get_status()

        git = repo.git

        try:
            status_str = git.status()
            status_porcelain = git.status('--porcelain')
        except Exception as e:
            message = "Error in git status: {}".format(str(e))
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

        status = {
            'output': status_str,
            'staged': staged,
            'unstaged': unstaged,
            'untracked_files': untracked_list
        }

        action_result.add_data(status)
        action_result.update_summary({'status': status_str.splitlines()[1]})
        return action_result.set_status(phantom.APP_SUCCESS)

    def _test_asset_connectivity(self, param):
        """ This function tests the connectivity of an asset with given credentials.

        :param param: (not used in this method)
        :return: status success/failure
        """

        action_result = ActionResult()
        self.save_progress(consts.GIT_CONNECTION_TEST_MSG)
        self.save_progress("Configured repo URI: {uri}".format(uri=self.repo_uri))

        # if http(s) URI and username or password is not provided
        if not self.ssh and not (self.username and self.password):
            self.save_progress(consts.GIT_USERNAME_AND_PASSWORD_REQUIRED)
            self.set_status(phantom.APP_ERROR, consts.GIT_TEST_CONNECTIVITY_FAIL)
            return action_result.get_status()

        remote_refs = []
        g = git.cmd.Git()

        # ls_remote function call the git command ls-remote
        try:
            repo_details = g.ls_remote(self.modified_repo_uri).split('\n')
        except:
            self.save_progress("Error while calling configured URI")
            if self.ssh:
                self.save_progress("Do you still need to run the configure_ssh action?")
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
            self.save_progress("Invalid branch name")
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

        if action in action_mapping.keys():
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
        print 'No test json specified as input'
        exit(0)
    with open(sys.argv[1]) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print json.dumps(in_json, indent=4)
        connector = GitConnector()
        connector.print_progress_message = True
        return_value = connector._handle_action(json.dumps(in_json), None)
        print json.dumps(json.loads(return_value), indent=4)
    exit(0)
