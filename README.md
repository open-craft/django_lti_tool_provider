# LTI Tool Provider

This is an implementation of [IMS LTI](http://www.imsglobal.org/toolsinteroperability2.cfm) Tool Provider in a from
of pluggable Django application

# Installation

It's not enough to add `django_lti_tool_provider` to requirements.txt. This version is built on top of ims_lti_py, 
which haven't been updated on PyPi for quite some time. What's worse, PyPi version is broken, but it is not visible 
until first LTI request is posted: there's a [typo][ims_lti_typo] that causes responses from ToolProvider to contain
well-formed, but invalid (in terms of LTI protocol) XML.

That's why, in order to get a working version, both `django_lti_tool_provider` and `ims_lti_py` need to be added to 
`requirements.txt`. Correct version of `ims_lti_py` can be obtained with

    -e git+https://github.com/tophatmonocle/ims_lti_py.git@979244d83c2e6420d2c1941f58e52f641c56ad12#egg=ims_lti_py-develop

[ims_lti_typo]: https://github.com/tophatmonocle/ims_lti_py/commit/0c5ff1eeb0fb68044642e4af4365461805bfd212#diff-7030333915c3863dcac5817c04f94215L182