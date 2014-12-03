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
# yum needs-restarting
Loaded plugins: needs-restarting
This system is receiving updates from RHN Classic or Red Hat Satellite.
You blacklisted:


No processes using old files, nice job.
```

System running some services using old files:
```
# yum needs-restarting
Loaded plugins: needs-restarting
You blacklisted:


You might want to restart the following processes:
httpd
sshd
```

System running processes having no init script using old files:
```
# yum needs-restarting
Loaded plugins: needs-restarting
You blacklisted:


You might want to restart the following processes:
? (PID 30799, unicorn worker[0] -D -E production -c /var/opt/gitlab/gitlab-rails/etc/unicorn.rb /opt/gitlab/embedded/service/gitlab-rails/config.ru)
? (PID 10053, unicorn worker[1] -D -E production -c /var/opt/gitlab/gitlab-rails/etc/unicorn.rb /opt/gitlab/embedded/service/gitlab-rails/config.ru)
? (PID 28486, unicorn master -D -E production -c /var/opt/gitlab/gitlab-rails/etc/unicorn.rb /opt/gitlab/embedded/service/gitlab-rails/config.ru)
? (PID 28650, nginx: worker process)
? (PID 28649, nginx: worker process)
? (PID 28648, nginx: master process /opt/gitlab/embedded/sbin/nginx -p /var/opt/gitlab/nginx)
? (PID 28584, sidekiq 2.17.0 gitlab-rails [0 of 25 busy])
```

Example configuration blacklisting various **GitLab** and ``nginx`` processes:
```
$ cat /etc/yum/pluginconf.d/needs-restarting.conf
[main]
enabled=1
excludeProcs=gitlab,nginx
```

Installation
============
A RPM package will follow soon. Currently you need to download the plugin and the plugin configuration and save it in the appropriate directory to make it work:

```
# curl https://raw.githubusercontent.com/stdevel/yum-plugin-needs-restarting/master/needs-restarting.py -o /usr/lib/yum-plugins/needs-restarting.py
# curl https://raw.githubusercontent.com/stdevel/yum-plugin-needs-restarting/master/needs-restarting.conf -o /etc/yum/pluginconf.d/needs-restarting.conf
# yum help needs-restarting
Loaded Plugins: needs-restarting
You blacklisted:


needs-restarting

List processes that are using old files
```
