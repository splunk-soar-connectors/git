**Unreleased**

* Prevent asset credentials from being sent to a caller-selected repository endpoint.
* Constrain repository names and clone destinations to the connector state directory.
* Reject out-of-repository file paths before add, update, or delete operations.
* Reject Git commit identities that could inject configuration sections.
* Require a pinned server host key for SSH repository connections.
