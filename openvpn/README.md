# openvpn server-client 实践过程

 因为有两台机器，一台阿里云 ubuntu 一台 腾讯云 centos，而且都是低配版本。
 
 一些服务就分散配置在两台上，想通过vpn连接在一起，组成局域网，不把服务暴漏出去，
 
 同时本地的电脑也可以访问这些服务，方便开发调试。
 
 
## VPN 选择
  一开始没有用VPN，是因为无论ubuntu还是centos 都没提供的简介的默认的server.conf 之类的，
  
  `apt-get/yum install openvpn` 之后，只有一个孤零零的openvpn
  
  偷懒心起，就围观了一堆VPN server软件的测评。
  
  - PPTP 
  - L2TP
  - openvpn
  - SoftEtherVPN
  - ....
   
 有的说这个不行，那个不稳定，就是要偏听偏信，最后筛掉剩，`SoftEtherVPN`，但是官网打不开，github文档也没有，看了一些文章也觉得操作太多，
 最后选定了`openvpn`([github](https://github.com/OpenVPN/openvpn))
 
## 安装

### 准备工作
在github 发现srever和cient用的同一个`openvpn`执行文件，就去release下载相关版本包，

down下来是源码，autoreconf 有几个环境需要设置，果断放弃。

找来找去，github的[README](https://github.com/OpenVPN/openvpn)上链接到[download页面](https://openvpn.net/index.php/download/community-downloads.html)，下载了`Source Tarball (gzip)`的[openvpn-2.3.12.tar.gz](https://swupdate.openvpn.org/community/releases/openvpn-2.3.12.tar.gz),在ubuntu 以及centos上就编译安装。

简单的三步

```sh
./configure
make
make install
```
可能要安装 ssl,lzo,libpam等依赖

可以通过像 `apt-cache/yum search ssl|grep dev|grep ssl` 这样，找到相应的包安装，

即 `libssl-dev` 和`openssl-devel`，`liblzo2-dev`和`lzo-devel`，
`libpam0g-dev` 和 `pam-devel`。

搜索出来的要注意看后面的说明，这里要的基本都是dev，开发包之类的。

### 部署流程


#### 1. CA以及公私秘钥生成

	内容基本上参考了这篇[月光博客／guest_server 投稿](http://www.williamlong.info/archives/3814.html) ，虽然许多命令以及一些东西变化了，但是基本流程一样。下面就按新的命令做一下。
   
	这基本是为服务端、客户端配证书和key，
 
	说一句， `easy-rsa` 感觉真的是**太好用了**，应该不仅限于openvpn这儿使用。
 
	软件包是在[github](https://github.com/OpenVPN/easy-rsa)上下的[release](https://github.com/OpenVPN/easy-rsa/releases) 3.0.1
 
 先测试`./easyrsa`
 
 ```bash
 bash$./easy-rsa
......
  init-pki
  build-ca [ cmd-opts ]
  gen-dh
  gen-req <filename_base> [ cmd-opts ]
  sign-req <type> <filename_base>
  build-client-full <filename_base> [ cmd-opts ]
  build-server-full <filename_base> [ cmd-opts ]
  revoke <filename_base>
  gen-crl
  update-db
  show-req <filename_base> [ cmd-opts ]
  show-cert <filename_base> [ cmd-opts ]
  import-req <request_file_path> <short_basename>
  export-p7 <filename_base> [ cmd-opts ]
  export-p12 <filename_base> [ cmd-opts ]
  set-rsa-pass <filename_base> [ cmd-opts ]
  set-ec-pass <filename_base> [ cmd-opts ]
......
 ```
这一列都是action命令。
 
 按照月光博客的步骤来制作证书，命令按照最新的来的
 
 不说证书、签名、RSA、公私钥这些了，自己去学，
 
 1. `./easyrsa init-pki` 生成环境
 2. `./easyrsa build-ca` 制作CA，这里需要设CA的密码
 3. `./easyrsa build-server-full xxx` 生成server xxx 公私钥，要设置一个密码，同时要用到上面那个密码
 4. `./easyrsa build-client-full clientxxx `生成客户端 clientxxx 公私钥，和上面差不多。
 5. `./easyrsa gen-dh` 生成 dh.pem 是一个2048位左右的素数，
 
 最后各个文件的用处见于下表
 
 <!--
 | 文件名 | 需要者 Needed By | 说明Purpose | 秘密 Secret |
| ca.crt | 服务端和所有客户端 server + all clients | 根证书 Root CA certificate | 否 NO |
| ca.key | 签发私钥的机器 key signing machine only | 根私钥  Root CA key | 是 YES |
| dh{n}.pem | 服务器 server only | Diffie Hellman parameters | 否 NO |
| server.crt | 服务器 server only | 服务器证书 Server Certificate | 否 NO |
| server.key | 服务器 server only | 服务器私钥 Server Key | 是 YES |
| client1.crt | client1 only | Clinet1的证书 Client1 Certificate | 否 NO |
| client1.key | client1 only | Clinet1的私钥 Client1 Key | 是 YES |
| client2.crt | client2 only | Client2的证书 Client2 Certificate | 否 NO |
| client2.key | client2 only | Client2的私钥 Client2 Key | 是 YES |
| client3.crt | client3 only | Client3的证书 Client3 Certificate | 否 NO |
| client3.key | client3 only | Client3的私钥 Client3 Key | 是 YES |
-->
 
 这里拷贝的原网页，就没有编辑成md表格
 
 <table cellspacing="0" cellpadding="8" border="1"> <tbody> <tr> <td>文件名</td> <td>需要者<br> Needed By</td> <td>说明<br> Purpose</td> <td>秘密<br> Secret</td> </tr> <tr> <td>ca.crt</td> <td>服务端和所有客户端<br> server + all clients</td> <td>根证书<br> Root CA certificate</td> <td>否<br> NO</td> </tr> <tr> <td>ca.key</td> <td>签发私钥的机器<br> key signing machine only</td> <td>根私钥<br> Root CA key</td> <td>是<br> YES</td> </tr> <tr> <td>dh{n}.pem</td> <td>服务器<br> server only</td> <td>Diffie Hellman parameters</td> <td>否<br> NO</td> </tr> <tr> <td>server.crt</td> <td>服务器<br> server only</td> <td>服务器证书<br> Server Certificate</td> <td>否<br> NO</td> </tr> <tr> <td>server.key</td> <td>服务器<br> server only</td> <td>服务器私钥<br> Server Key</td> <td>是<br> YES</td> </tr> <tr> <td>client1.crt</td> <td>client1 only</td> <td>Clinet1的证书<br> Client1 Certificate</td> <td>否<br> NO</td> </tr> <tr> <td>client1.key</td> <td>client1 only</td> <td>Clinet1的私钥<br> Client1 Key</td> <td>是<br> YES</td> </tr> <tr> <td>client2.crt</td> <td>client2 only</td> <td>Client2的证书<br> Client2 Certificate</td> <td>否<br> NO</td> </tr> <tr> <td>client2.key</td> <td>client2 only</td> <td>Client2的私钥<br> Client2 Key</td> <td>是<br> YES</td> </tr> <tr> <td>client3.crt</td> <td>client3 only</td> <td>Client3的证书<br> Client3 Certificate</td> <td>否<br> NO</td> </tr> <tr> <td>client3.key</td> <td>client3 only</td> <td>Client3的私钥<br> Client3 Key</td> <td>是<br> YES</td> </tr> </tbody></table>
 
  说一句，这个制作在哪儿制作都可以，最好在常用电脑上，注意保护好CA私钥就是了  
  
  此外根据下面2的配置，使用`openvpn --genkey --secret ta.key`生成了一份`ta.key`  
  用于 tls 好像 

#### 2. server.conf 配置
  
  从`openvpn-2.3.12/sample/sample-config-files`处拷出一份 server.conf，
  
  server.conf 的配置说明见于[这篇](http://www.woyaohuijia.cn/show/121.html)
  
  就不说了，说下我的对原文件的改动的部分。
  
  ```conf
  local 我的机器的公网
  ca ca.crt 上一个生成的CA公钥，
  cert server.crt 上面生产的server公钥
  key server.key  # This file should be kept secret，
  dh dh.pem 上面生成的素数文件
  server 修改了这里，选了一个小一点不常见的范围，
  client-to-client 开启了这个，测试一下
  tls-auth ta.key 0 # This file is secret,上面生成的
  max-clients 3  设了少一点
  user nobody  运行用户
  group nogroup 运行组
  status openvpn-status.log
  log         openvpn.log
  log-append  openvpn.log
  ```
  
  启动 `openvpn --config server.conf`
  需要密码，是server秘钥的密码，输入就是了，这是在另一个窗口开始 ifconfig 即可看到生成的网络端口
  
#### 3. server 运行
  
  因为要输入server 的密码，同时也需要后台运行
  查看  `openvpn --help` ,看有哪些选项，

  最好找到了 `--askpass [file]` ，就把密码存入文件，然后加上这个选项成功了
  
  编辑server.conf 试试能不能配置 `askpass xxx.txt`，也ok，
  
  `--cd dir` 运行时移到某个目录，当然是配置的目录
  
  `--cd /usr/local/openvpn` 感觉需要先cd 才能找到server.conf 所以没有写
  
  `--writepid file` pid file，把`writepid /run/openvpn.pid`写入server.conf
  
  `--daemon` ，把`daemon` 写入server.conf

  运行之后，可以，就还想写一个[init.d](./init.d)的管理工具
   
  贴一部分代码[init.d/openvpn](./init.d/openvpn.server)
  
  ```sh
  #!/bin/sh

  PIDFILE=/run/openvpn.pid

 start_server () {
    if [ -f $PIDFILE ]
    then
        echo 'already started'
        exit 3 
    else
        echo 'starting'
        openvpn --cd /usr/local/openvpn/ --config server.conf;
        echo 'sucess'
    fi
}

 stop_server () {
    if [ -f $PIDFILE ]
    then
        echo 'kill process '`cat $PIDFILE`
        kill `cat $PIDFILE`
        rm $PIDFILE
    else
        echo 'pid file not exists'
        exit 2
    fi
}

 restart_server() {
    stop_server
    start_server
}
  ```
  大致这个样子
  
  `/etc/init.openvpn start|stop|restart`
  

#### 4. client 配置／连接
  
   同样从`openvpn-2.3.12/sample/sample-config-files`处拷出一份 client.conf，
  
   然后编辑，基本改动比较少，有些选项照抄server 即可
  
  如下是改动的部分
  
  ```conf
  remote xx.xx.xx.xx 1194
  user nobody
  group nobody
  ca ca.crt  你的CA公钥
  cert clientxx.crt 的公钥
  key clientxx.key 的私钥 
  tls-auth ta.key 1 切记这个ta.key 是在server上生成的，不要漏掉
  #额外添加的log
  log openvpn.log
  log-append  openvpn.log
  status openvpn-status.log
  #运行的
  writepid /run/openvpn.pid
  daemon
  # 在 easyrsa 那一步输入的密码，
  askpass pass.client.txt 
  ```
  
  openvpn --config client.conf 即可
  
  同时照例可以编写出[init.d/openvpn](./init.d/openvpn.client)
  
  `/etc/init.d/openvpn start|stop|restart`
  
  运行后即可看到连接的IP，

### 使用
#### 1. 固定IP设置
   
   因为是两台主机，要交互，所以要给client机器配上固定的IP，
   看了下 要编辑 ipp.txt
   
   同时在server.conf 取消相关注释，得到
   `ifconfig-pool-persist ipp.txt`
   
   ipp.txt 内容是一行行的name,IP，比如这里就是
   `client0,xx.xx.xx.xx`
   
   因为`client0` 是`easyrsa`制作客户端秘钥对时用的名字，
   
   好像是因为`easyrsa`机智的把name和common name 合并成简单的一个。
   
   来回调试时，发现好像IP只能间隔大于4个，，比如
   
   ```txt
   client0,xx.xx.xx.4 
   client1,xx.xx.xx.8
   ```
   这样子的。。。可能是新的要求吧，以后再看官方文档研究了
  
#### 2. 其他

   可以把相关`/etc/init.d/openvpn` 加入到 启动项，或者是调整参数，retry之类的，
   
   以后再弄。
   

## 结论
   
   1. 新版本就是好，比以前简单优雅
   2. 多看 --help 
   3. 了解原理还是比较快的 
 
`easyrsa` 真是简直不要太简洁方便的了，


    
    
   
  
  

   
  
  
  
  