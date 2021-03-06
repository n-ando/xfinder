# xfinder

RaspberryPi はヘッドレス状態 (モニタ、キーボードを接続しない状態) ではIPアドレスなどを知る術がないため初期設定を行うのは少々困難です。
最初にモニタとキーボードを接続して、ホスト名を設定し前述のようにAvahi経由でIPアドレスをホスト名から知ることも可能ですが、全く設定していないRaspberryPiについてはこの方法も使えません。

<a id="anchor1"></a>
## xfinder とは

xfinder はRaspberryPiやBeagleBoneなどのCPUボードに搭載されているEthernetインターフェースのMAC (Media Access Control) アドレスからIPアドレスを割出しログインするためのツールです。

Ethernetのインターフェースには48ビットの固有のアドレス(MAC (Media Access Control) アドレス)が割り振られており、その上位24ビットはベンダ(ネットワーク機器を開発する企業など)の固有のアドレスとなっています。Ethernetではパケットの送受信をするために相互にMACアドレスを知る必要があり、IPアドレスからMACアドレスを調べるためのARP(Address Resolution Protocol)と呼ばれるプロトコルが利用できます。
xfinderでは、ネットワーク上に接続されている特定のMACアドレスのパターンを見つけることにより、RaspberryPiなどのヘッドレスシステムのIPアドレスを調べ、ssh等でログインし設定・開発を容易に行えるようにサポートします。

<div style="text-align: center;"><img src="raspberrypi_and_arp.png" width="600px"></div>
<div style="text-align: center;"><b>xfinderでRaspberryPiを見つける</b></div>


xfinderは一つの実行ファイルでコマンドラインツール (CUI モード) とグラフィカルユーザインターフェースツール (GUI モード) の2通りとして利用することができます。
ここでは、GUIモードのxfinderの使い方について説明します。

<a id="anchor2"></a>
## xfinderの動作条件

xfinderは以下の環境で動作します。

| OS          | Python    | Terminal ソフトウェア |
| Windows 10  | Python3   | Tera Term, PuTTY, Poderosa |
| MacOS X     | Python3   | Terminal.app, iTerm.app |
| Linux (Ubuntu18.04,20.04で動作確認) | Python3 | gnome-terminal, xterm, kterm |

なお、単一バイナリ形式 (WindowsのEXE, MacOSのapp、Linuxの単一事項ファイル）ではPython3のインストールは不要です。

<a id="anchor2"></a>
## xfinderのダウンロード

xfinder 以下の場所からダウンロードできます。

| ''xfinderバイナリ'' | [https://github.com/n-ando/xfinder/releases](https://github.com/n-ando/xfinder/releases) |
| ''Windows''       | [https://github.com/n-ando/xfinder/releases/download/1.1/xfinder.exe](https://github.com/n-ando/xfinder/releases/download/1.1/xfinder.exe)]
| ''MacOS X''       | [https://github.com/n-ando/xfinder/releases/download/1.1/xfinder_v1.1.dmg](https://github.com/n-ando/xfinder/releases/download/1.1/xfinder_v1.1.dmg)|
| ''Linux'' (Ubuntu18.04, 20.04で動作確認) | [https://github.com/n-ando/xfinder/releases/download/1.1/xfinder](https://github.com/n-ando/xfinder/releases/download/1.1/xfinder)|
| ''xfinderソースコード''       | [https://github.com/n-ando/xfinder](https://github.com/n-ando/xfinder) |

<div style="text-align: center;"><img src="xfinder_folder.png" width="600px"></div>
<div style="text-align: center;"><b>ダウンロードした xfinder</b></div>

<a id="anchor3"></a>
## xfinder (GUIモード) を使う

xfinderの使い方は以下の3ステップです。

1. ネットワークをスキャンしてRaspberryPi等を見つける
1. スキャンして見つかったRaspberryPiを確認する
1. TeraTerm等ターミナルソフトウエアでログインして作業をする

<a id="anchor4"></a>
### xfinder の起動

xfinder.exeを起動すると、以下の様な画面が表示されます。

<div style="text-align: center;"><img src="xfinder_gui_panes.png" width="600px"></div>
<div style="text-align: center;"><b>xfinder の GUI画面</b></div>

まず、①左上のペインにてスキャンする条件（インターフェース、ボード、MACアドレスパターン等）を指定しスキャンを開始、②次にスキャンして見つかったRaspberryPi等のリストが表示されるので選択、③の左下のペインにてログイン条件を指定してターミナルアプリケーションを起動します。
ターミナルアプリケーションが起動後は、対象となるRaspberryPiにログインして設定やプログラムの開発などを行うことができます。

なお、右のペインに表示されたボードのリストをダブルクリックすることでターミナルアプリケーションの起動とログインを行うことも可能です。

<a id="anchor5"></a>
### Scan settings

左上の ''Scan settings'' では、ネットワークをスキャンするための条件を設定します。

<a id="anchor6"></a>
#### Interface address

現在のPCのどのネットワークインターフェースからRaspberryPiを探すかを選択します。複数のネットワークインターフェースがある場合、複数のIPアドレスが表示されるので、どのネットワーク(例えば、一つはグローバル側、もう一つがプライベート側のネットワークにつながっており、プライベート側のネットワークにあるRaspberryPiを探したい場合はここでプライベートアドレスを選択します。)をスキャンするかを選択します。

<div style="text-align: center;"><img src="xfinder_select_ifaddr.png" width="600px"></div>
<div style="text-align: center;"><b>Interface addressでスキャンするネットワークインターフェースのIPアドレスを指定する</b></div>

全てのネットワークインターフェースに対してスキャンを行う場合は''ALL''を選択してください。
どのIPアドレスがどのネットワークインターフェースと対応しているかわからない場合は、''コントロールパネル''→''ネットワークとインターネット''→''ネットワークと共有センター''→''アダプターの設定の変更''からアダプタのアイコンをクリックしてどのようなIPアドレスが割り当てられているか確認してください。

また、コマンドプロンプトを開いて ''ipconfig'' コマンドを実行しインターフェースと割り当てられているIPアドレスを確認することもできます。

<a id="anchor7"></a>
#### Board type

どのボードを探すかコンボボックスから選択します。RaspberryPiかBeagleBoneを選択でき、デフォルトではRaspberryPiが選択されています。

<div style="text-align: center;"><img src="xfinder_select_board.png" width="600px"></div>
<div style="text-align: center;"><b>スキャンするボードタイプを指定する</b></div>

この一覧に探したいボードがない場合は、該当するボードのネットワークインターフェースのMACアドレスの上6ケタを調べ、次のMatch Patternのテキストボックスに入力しスキャンする必要があります。

RaspberryPiにUSB無線LANアダプタを付け、無線LANのみで接続している場合はここでRaspberryPiを選択しても探すことはできません。
無線LANアダプタのMACアドレスのMACアドレスの上6ケタ (例えば Buffaroの場合10:6f:3f) をMatch Patternに入力して探します。

<a id="anchor8"></a>
#### Match pattern

RaspberryPiやBeagleBone以外のボードを探す場合、ここに探したいMACアドレスのパターンを入力します。

#ref(xfinder_select_pattern.png,80%,center)
CENTER: ''スキャンするMACアドレスのパターンを指定する''

またRaspberryPiに無線LANアダプタなどを装着している場合も、メーカー固有のMACアドレス上6ケタを入力することで探し出すことが可能です。
ただし、メジャーなメーカーの無線LANアダプタなどはスキャンすると多数発見されることもあります。


<a id="anchor9"></a>
#### Scanボタン/Abortボタン

''Scan'' ボタンはスキャンを実行する際に押します。スキャン中は押すことができません。
''Abort''ボタンはスキャン実行中に途中でやめたい場合に押します。スキャン実行中のみ押すことができます。
ボタンの下のプログレスバーはスキャンの進捗状況を表示します。

<div style="text-align: center;"><img src="xfinder_scanning_board.png" width="600px"></div>
<div style="text-align: center;"><b>スキャン実行時</b></div>

<a id="anchor10"></a>
### Found nodes

右側の ''Found nodes'' のペインはスキャンして見つかったボードのIPアドレス、MACアドレスおよびホスト名を表示します。

- ''IP address'': 見つかったボードのIPアドレスを表示します。ヘッダ部分を押すとIPアドレス順でソートします。
- ''MAC address'': 見つかったボードのMACアドレスを表示します。ヘッダ部分を押すとMACアドレス順でソートします。
- ''Host name'': 見つかったボードのホスト名を表示します。ヘッダ部分を押すとホスト名順でソートします。

なお、ここに表示されたリストをダブルクリックすると、左の ''Terminal launcher'' の設定に従ってターミナルアプリケーションが起動しログインできます。

<div style="text-align: center;"><img src="xfinder_launchterm_dclick.png" width="600px"></div>
<div style="text-align: center;"><b>Found nodesから直接ターミナルアプリケーションを起動する</b></div>

<a id="anchor11"></a>
### Terminal launcher

左側の ''Terminal launcher'' のペインは見つかったホストに対してターミナルアプリケーションを利用してログインする際に使用します。

- ''User name'': ログイン時に使用するユーザ名を入力します。左上の''Scan setting'' の ''Board type'' 設定によって自動的に値が入力されます。
- ''Password'': ログイン時に使用するパスワードを入力します。左上の''Scan setting'' の ''Board type'' 設定によって自動的に値が入力されます。
- ''Port'': ログイン時に使用するポート番号を入力します。デフォルトではsshのデフォルトポート番号22が設定されています。
- ''Terminal App'': 使用するターミナルアプリケーションがコンボボックスから選択で来ます。利用可能なターミナルアプリケーションはWindowsでは ''TeraTerm'', ''Poderosa'', ''PuTTY'' のいずれかで、起動時にこれらがインストールされているかチェックし、利用可能なものだけリストに表示されます。
- ''Login''ボタン: 右側のFound nodesでログインするノード選択すると押下可能になります。このボタンを押すと、上の設定に従ってターミナルアプリケーションが起動されRaspberryPiにログインできます。

|ボードタイプ | User name | Password |
| RaspberryPi | pi        | raspberry|
| BeagleBone  | root      | (パスワード無し) |



<div style="text-align: center;"><img src="xfinder_launcterm_by_loginbutton.png" width="600px"></div>
<div style="text-align: center;"><b>Loginボタンを押してターミナルアプリケーションを起動する</b></div>

<div style="text-align: center;"><img src="launch_teraterm.png" width="600px"></div>
<div style="text-align: center;"><b>起動したターミナルアプリケーション (TeraTerm Pro)</b></div>

### Terminalの利用

TerminalペインのTerminalプルダウンには、インストールされているTerminalソフトウェアを自動的に判別して表示します。
したがって、Terminalソフトウェアを使ってRaspberryPi などにログインしたい場合は、必要なTerminalソフトウェアをインストールしてください。
利用可能なTerminalソフトウェアは、以下の表に示すとおりOSごとに決まっています。もし、追加してほしいTerminalソフトウェアがある場合は、GitHubのissueで要望してください。

| OS          | Python    | Terminal ソフトウェア |
| Windows 10  | Python3   | Tera Term, PuTTY, Poderosa |
| MacOS X     | Python3   | Terminal.app, iTerm.app |
| Linux (Ubuntu18.04,20.04で動作確認) | Python3 | gnome-terminal, xterm, kterm |

#### Terminal ソフトウェアの入手先

- Windows
  - Tera Term Pro: https://ja.osdn.net/projects/ttssh2/
  - PuTTY: https://www.putty.org/
  - Poderosa: https://ja.poderosa-terminal.com/
- MacOS X
  - Terminal: MacOS Xにデフォルトでインストールされているソフトウェア
  - iTerm: https://iterm2.com/
    - Home Brew が入っている場合は brew cask install iterm2 でインストール可能
- Linux
  - gnome-terminal: Ubuntu Linuxなどではデフォルトでインストールされています
  - xterm: 以下のコマンドでインストール可能です
    - deb系 (Debian, Ubuntu等）: apt install xterm
    - rpm系 (RedHat, CentOS等）: yum install xterm
  - kterm: 以下のコマンドでインストール可能です
    - deb系 (Debian, Ubuntu等）: apt install kterm
    - rpm系 (RedHat, CentOS等）: yum install kterm

利用可能なTerminalソフトウェアは、以下の表に示すとおりOSごとに決まっています。もし、追加してほしいTerminalソフトウェアがある場合は、GitHubのissueで要望してください。ソフトウェア
利用可能なTerminalソフトウェアは、以下の表に示すとおりOSごとに決まっています。もし、追加してほしいTerminalソフトウェアがある場合は、GitHubのissueで要望してください。
