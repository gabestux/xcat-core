Summary: Meta-package for a common, default xCAT setup
Name: xCAT
Version: %(cat Version)
Release: snap%(date +"%Y%m%d%H%M")
License: EPL
Group: Applications/System
Vendor: IBM Corp.
Packager: IBM Corp.
Distribution: %{?_distribution:%{_distribution}}%{!?_distribution:%{_vendor}}
Prefix: /opt/xcat
BuildRoot: /var/tmp/%{name}-%{version}-%{release}-root
#BuildArch: noarch
Source1: xcat.conf
Source2: postscripts.tar.gz
Source3: templates.tar.gz
Source5: xCATMN 

%ifos linux
Source4: prescripts.tar.gz
%endif

Provides: xCAT = %{version}
Conflicts: xCATsn
Requires: xCAT-server xCAT-client perl-DBD-SQLite

%ifos linux
Requires: dhcp httpd nfs-utils expect nmap fping bind perl-XML-Parser vsftpd perl(CGI)
Requires: /etc/xinetd.d/tftp
%ifarch s390x
# No additional requires for zLinux right now
%else
# yaboot-xcat is pulled in so any MN can manage ppc nodes
Requires: conserver-xcat yaboot-xcat perl-Net-Telnet
%endif
%ifarch ppc64
Requires: perl-IO-Stty
%endif
%ifarch ppc64 x86_64
Requires: openslp-xcat
%endif
%endif

%ifarch i386 i586 i686 x86 x86_64
# All versions of the nb rpms are pulled in so an x86 MN can manage nodes of any arch.
# The nb rpms are used for dhcp-based discovery, and flashing, so for now we do not need them on a ppc MN.
Requires: syslinux xCAT-genesis-x86_64 elilo-xcat
Requires: ipmitool-xcat >= 1.8.9
Requires: xnba-undi syslinux-xcat
%endif

%description
xCAT is a server management package intended for at-scale management, including
hardware management and software management.

%prep
%ifos linux
tar zxf %{SOURCE2}
tar zxf %{SOURCE4}
%else
rm -rf postscripts
cp %{SOURCE2} /opt/freeware/src/packages/BUILD
gunzip -f postscripts.tar.gz
tar -xf postscripts.tar
%endif

%build

%pre
if [ -e "/etc/SuSE-release" ]; then
    # In SuSE, dhcp-server provides the dhcp server, which is different from the RedHat.
    # When building the package, we cannot add "dhcp-server" into the "Requires", because RedHat doesn't 
    # have such one package.
    # so there's only one solution, Yes, it looks ugly.
    rpm -q dhcp-server >/dev/null
    if [ $? != 0 ]; then
        echo ""
        echo "!! On SuSE, the dhcp-server package should be installed before installing xCAT !!"
        exit -1;
    fi
fi
# only need to check on AIX
%ifnos linux
if [ -x /usr/sbin/emgr ]; then          # Check for emgr cmd
	/usr/sbin/emgr -l 2>&1 |  grep -i xCAT   # Test for any xcat ifixes -  msg and exit if found
	if [ $? = 0 ]; then
		echo "Error: One or more xCAT emgr ifixes are installed. You must use the /usr/sbin/emgr command to uninstall each xCAT emgr ifix prior to RPM installation."
		exit 2
	fi
fi
%endif



%install
mkdir -p $RPM_BUILD_ROOT/etc/apache2/conf.d
mkdir -p $RPM_BUILD_ROOT/etc/httpd/conf.d
mkdir -p $RPM_BUILD_ROOT/install/postscripts
mkdir -p $RPM_BUILD_ROOT/install/prescripts
mkdir -p $RPM_BUILD_ROOT/install/kdump
mkdir -p $RPM_BUILD_ROOT/%{prefix}/share/xcat/
cd $RPM_BUILD_ROOT/%{prefix}/share/xcat/

%ifos linux
tar zxf %{SOURCE3}
%else
cp %{SOURCE3} $RPM_BUILD_ROOT/%{prefix}/share/xcat
gunzip -f templates.tar.gz
tar -xf templates.tar
rm templates.tar
%endif

cd -
cd $RPM_BUILD_ROOT/install

%ifos linux
tar zxf %{SOURCE2}
tar zxf %{SOURCE4}
%else
cp %{SOURCE2} $RPM_BUILD_ROOT/install
gunzip -f postscripts.tar.gz
tar -xf postscripts.tar
rm postscripts.tar
%endif

chmod 755 $RPM_BUILD_ROOT/install/postscripts/*

rm LICENSE.html
mkdir -p postscripts/hostkeys
cd -
cp %{SOURCE1} $RPM_BUILD_ROOT/etc/apache2/conf.d/xcat.conf
cp %{SOURCE1} $RPM_BUILD_ROOT/etc/httpd/conf.d/xcat.conf
cp %{SOURCE5} $RPM_BUILD_ROOT/etc/xCATMN

mkdir -p $RPM_BUILD_ROOT/%{prefix}/share/doc/packages/xCAT
cp LICENSE.html $RPM_BUILD_ROOT/%{prefix}/share/doc/packages/xCAT

%post
%ifnos linux
. /etc/profile
%else
cp -f $RPM_INSTALL_PREFIX0/share/xcat/scripts/xHRM /install/postscripts/
. /etc/profile.d/xcat.sh
%endif
if [ "$1" = "1" ]; then #Only if installing for the first time..
$RPM_INSTALL_PREFIX0/sbin/xcatconfig -i
else
$RPM_INSTALL_PREFIX0/sbin/xcatconfig -u
fi
exit 0

%clean

%files
%{prefix}
# one for sles, one for rhel. yes, it's ugly...
/etc/httpd/conf.d/xcat.conf
/etc/apache2/conf.d/xcat.conf
/etc/xCATMN
/install/postscripts
/install/prescripts
%defattr(-,root,root)

%postun
if [ "$1" = "0" ]; then
%ifnos linux
if grep "^xcatd" /etc/inittab >/dev/null
then
/usr/sbin/rmitab xcatd >/dev/null
fi
%endif
true    # so on aix we do not end up with an empty if stmt
fi

