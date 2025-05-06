ifconfig enp1s0f0np0 up
ip addr add 192.168.40.1/24 dev enp1s0f0np0
ifconfig enp1s0f0np0 mtu 9000

ifconfig enp1s0f1np1 up
ip addr add 192.168.50.1/24 dev enp1s0f1np1
ifconfig enp1s0f1np1 mtu 9000

ifconfig enp2s0f0np0 up
ip addr add 192.168.60.1/24 dev enp2s0f0np0
ifconfig enp2s0f0np0 mtu 9000

ifconfig enp2s0f1np1 up
ip addr add 192.168.70.1/24 dev enp2s0f1np1
ifconfig enp2s0f1np1 mtu 9000

ifconfig -a
uhd_find_devices
