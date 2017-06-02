Test Project
============

This is just a experimental prototype for the technique discussion purpose,
mainly for performance enhancement compare with
`xcat2 <https://github.com/xcat2/xcat-core>`_. It leverage the basic framework
of python-ironicclient, works as CLI for
`xcat3 <https://github.com/chenglch/xcat3>`_.

Supported operating systems:
============================

* Ubuntu 14.04, 16.04
* Redhat >= 7.0

Setup
=====

Please refer the link `xcat-play <https://github.com/chenglch/xcat-play>`_ to
setup python-xcat3client with ansible playbook.

Enable the environment variable defined in `/etc/profile.d/xcat3.sh` ::

  source /etc/profile.d/xcat3.sh


Command Example
===============

ENV
----

If you setup python-xcat3client manually please import the environment variable
manually. ::

  export XCAT3_URL=http://<api_ip>:<api_port>

Basic Usage
------------
::

    root@c910f05c01bc02k70:~# xcat3 --help
    usage: xcat3 [--version] [--debug] [--json] [-v] [--xcat3-url XCAT3_URL]
             [--max-retries MAX_RETRIES] [--retry-interval RETRY_INTERVAL]
             <subcommand> ...

    Command-line interface to xCAT3 API.

    Positional arguments:
      <subcommand>
        bootdev             Set/Get next boot device (net or disk or cdrom).
        create              Enroll node(s) into xCAT3 service
        delete              Unregister node(s) from the xCAT3 service.
        deploy              Deployment service for nodes (not complete)
        export              Export node(s) information as a specific json data
                            file
        import              Import node(s) information from json data file
        list                List the node(s) which are registered with the xCAT3
                            service.
        power               Power operation on/off/reset/status for nodes
        show                Show detailed information about node(s).
        update              Update information about registered node(s).
        network-create      Register network into xCAT3 service.
        network-delete      Unregister network from xCAT3 service.
        network-list        List the network(s) which are registered with the
                            xCAT3 service.
        network-show        Show detailed information about network.
        network-update      Update information about registered network(s).
        nic-create          Register nic into xCAT3 service.
        nic-delete          Unregister nic from xCAT3 service.
        nic-list            List the nic(s) which are registered with the xCAT3
                            service.
        nic-show            Show detailed infomation about nic.
        nic-update          Update information about registered nic(s).
        osimage-delete      Unregister osimage from xCAT3 service.
        osimage-list        List the osimage(s) which are registered with the
                            xCAT3 service.
        osimage-show        Show detailed information about osimage.
        osimage-update      Update information about registered osimage.
        service-list        List the service(s) which are registered with the
                            xCAT3 service.
        service-show        Show detailed information about service.
        passwd-create       Register passwd into xCAT3 service.
        passwd-delete       Unregister passwd from xCAT3 service.
        passwd-list         List the passwd(s) which are registered with the xCAT3
                            service.
        passwd-show         Show detailed information about passwd.
        passwd-update       Update information about registered passwd.

Create Node
-----------

- Create node with nics
::

  xcat3 create --mgt ipmi --netboot pxe --arch x86_64 \
  --nic mac=43:87:0a:05:00:00,ip=12.0.0.1,name=eth0 \
  --nic mac=43:87:0a:05:00:01,ip=13.0.0.1,name=eth1 \
  --control bmc_address=11.0.0.0,bmc_password=password,bmc_username=admin node0

- Create nodes with noderange
::

  xcat3 create --mgt kvm --netboot pxe --arch ppc64le  --control bmc_password=password,bmc_username=admin node[1-25]

Update Node
------------

- Update node range seperated by comma

::

  xcat3 update node2,node1 type=node control/bmc_address=admin control/bmc_password= mgt=ipmi

- Update node node range with [ - ] like xcat2

::

  xcat3 update node[1-16],node[17-24]  control/bmc_password=passw0rd control/bmc_username=admin


List Node
---------

- List all the nodes
::

   xcat3 list

- List specific nodes
::

  xcat3 list node[1-2],node[4-5]

Show Node Detail
----------------

- Show all the fields of nodes
::

  xcat3 show node1      # only show one node
  xcat3 show node[1-3]  # support show detail for node range

- Show specific fields of nodes
::

   xcat3 show node1 --fields mgt,netboot
   xcat3 show node[1-2] --fields control,mgt
   xcat3 show node1 --fields mgt,nics

   [
    {
        "node": "node1",
        "attr": {
            "mgt": "ipmi",
            "nics_info": {
                "nics": [
                    {
                        "ip": "12.0.0.1",
                        "mac": "42:87:0a:05:00:01",
                        "extra": {
                            "primary": true
                        },
                        "uuid": "c61b6785-a6ac-4892-a9a0-9acdadfe8037",
                        "name": "eth0"
                    },
                    {
                        "ip": "13.0.0.1",
                        "mac": "43:87:0a:05:00:01",
                        "extra": {},
                        "uuid": "b022f098-8efa-4819-8110-d3b767320e56",
                        "name": "eth1"
                    }
                ]
            },
            "name": "node1"
        }
    }
   ]

Delete Node
-----------
::

  xcat3 delete node[1-25]


Export Node
-----------
::

  xcat3 export node[1-2] -o /tmp/node1_2.json

Import Node
-----------
::

  xcat3 import /tmp/node1_2.json

Get Power
---------
::

  root@xxxxx# xcat3 power node0,xcat3test1 status
  node0: on
  xcat3test1: on

  Success: 2  Total: 2
