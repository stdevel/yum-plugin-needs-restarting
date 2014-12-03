yum-plugin-needs-restarting
===========================

**yum-plugin-needs-restarting** is a YUM plugin for listing processes using old files after upgrading your system.
It is based on the code of ``needs-restarting`` which is part of the ``yum-utils`` package.

I decided to create a YUM plugin for this purpose because I really missed something like ``zypper ps`` (*openSUSE, SUSE Linux Enterprise Server/Desktop*) on Fedora and Enterprise Linux (*Red Hat Enterprise Linux, CentOS, ScientificLinux,...*)

Features
========
The plugin checks for processes which are part of installed RPM packages and use deleted files. It is also possible to blacklist particular processes by specifying wildcards.
The plugin implements a new YUM command: ``needs-restarting``.

Examples
========
System having no processes using old files:
```

```

System running some services using old files:
```
```

System running processes (*services and processes having no init script*) using old files:
```
```

Example configuration blacklisting various **GitLab** processes:
```
```

Installation
============
