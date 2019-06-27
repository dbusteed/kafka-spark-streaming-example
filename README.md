# Kafka + Spark Streaming Example

This is an example of building a Proof-of-concept for Kafka + Spark streaming from scratch. This is meant to be a resource for video tutorial I made, so it won't go into extreme detail on certain steps. It can still be used as a follow-along tutorial if you like.

Also, this isn't meant to explain the design of Kafka/Hadoop, instead it's an actual hands-on example. I'd recommend learning the basics of these technologies before jumping in.

When considering this POC, I thought Twitter would be a great source of streamed data, plus it would be easy to peform simple transformations on the data. So for this example, we will 
* create a stream of tweets that will be sent to a Kafka queue
* pull the tweets from the Kafka cluster
* calculate the character count and word count for each tweet
* save this data to a Hive table

To do this, we are going to set up an environment that includes 
* a single-node Kafka cluster
* a single-node Hadoop cluster
* Hive and Spark

<!-- ![Kafka Diagram](https://kafka.apache.org/images/kafka-apis.png) -->

## 1. VM Setup

Although you might be able to follow along on your host computer (depending on your OS), I'd recommend setting up a virtual machine. 

I used a [Lubuntu 19.04](https://lubuntu.net/downloads/) VM on [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and gave it 4 GiB memory and 15 GiB storage, but feel free to use your favorite Linux distro. 

You will need internet access from this VM so make sure that is configured correctly. If this is your first time using VBox, you might also want to look into installing the guest additions that allow full screen use. 

## 2. Install Kafka 

"Installing" Kafka is done by downloading the code from one of the several mirrors. After finding the latest binaries from [the downloads page](https://kafka.apache.org/downloads), choose one of the mirror sites and `wget` it into your home directory. 

``` bash
~$ wget http://apache.claz.org/kafka/2.2.0/kafka_2.12-2.2.0.tgz
```

After that you will need to unpack it. At this point, I also like to rename the Kafka to something a little more concise.

``` bash
~$ tar -xvf kafka_2.12-2.2.0.tgz
~$ mv kafka_2.12-2.2.0.tgz kafka
```

Before continuing with Kafka, we'll need to install Java.

``` bash
~$ sudo apt install openjdk-8-jdk -y
```

Test the Java installation by checking the version. 

``` bash
~$ java -version
```

Now you can `cd` into the `kafka/` directory and start a Zookeeper instance, create a Kafka broker, and publish/subscribe to topics. You can get a feel for this by walking thru the [Kafka Quickstart](https://kafka.apache.org/quickstart), but it will also be covered later in this example.

While we are here, we should install a Python package that will allow us to connect to our Kafka cluster. But first, you'll need to make sure that you have Python 3 and `pip` installed on your system. For Lubuntu, Python 3 was already installed and accessible with `python3`, but I had to install `pip3` with 

``` bash
~$ pip3 install kakfa-python 
```

Confirm this installation with 

``` bash
~$ pip3 list | grep kafka
```


## 3. Install Hadoop

Similar to Kafka, we first need to download the binaries from a mirror. All releases can be found [here](https://hadoop.apache.org/releases.html). I used Hadoop 2.8.5. Select a mirror, download it, then unpack it to your home directory. 
* NOTE: I wrote out this step as using `wget`, but feel free to download the tar thru a browser (sometimes it is faster i think)
* NOTE #2: Again, I renamed my directory for convenience. 

``` bash
~$ wget https://archive.apache.org/dist/hadoop/common/hadoop-2.8.5/hadoop-2.8.5.tar.gz
~$ tar -xvf hadoop-2.8.5.tar.gz
~$ mv hadoop-2.8.5.tar.gz hadoop
~$ cd hadoop
~/hadoop$ pwd
/home/<USER>/hadoop
```

Edit `.bashrc` found in your home directory, and add the following.

``` bash
export HADOOP_HOME=/home/<USER>/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HADOOP_HDFS_HOME=$HADOOP_HOME
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

Be sure to insert your username on the first line, for example, for me it is `export HADOOP_HOME=/home/davis/hadoop`. Also, double check that your `$JAVA_HOME` is correct. This should be the default install location, but it may go somewhere else.

Also also, remember to execute your `.bashrc` after editing it so that the changes take place (this will be important later on)

``` bash
~$ source .bashrc
```

Next, we will need to edit/add some configuration files. From the Hadoop home folder (the one named `hadoop` that is in your home directory), `cd` into `etc/hadoop`.

Add the following to `hadoop-env.sh`

``` bash
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_CONF_DIR=${HADOOP_CONF_DIR:-"/home/<USER>/hadoop/etc/hadoop"}
```

Replace the file `core-site.xml` with the following:

``` xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.default.name</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

Replcae the file `hdfs-site.xml` with the following:

``` xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.permission</name>
        <value>false</value>
    </property>
</configuration>
```

As mentioned earlier, we are just setting up a single-node Hadoop cluster. This isn'y very realistic, but it works for this example. For this to work, we need to allow our machine to SSH into itself.

First, install SSH with 

``` bash
~$ sudo apt install openssh-server openssh-client -y
```

Then, set up password-less authentication

``` bash
~$ ssh-keygen -t rsa
~$ cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

Then, try SSH-ing into the machine (type `exit` to quit the SSH session and return)

``` bash
~$ ssh localhost
```

With Hadoop configured and SSH setup, we can start the Hadoop cluster and test the installation.

``` bash
~$ hdfs namenode -format
~$ start-dfs.sh
```

NOTE: These commands should be available anywhere since we added them to the PATH during configuration. If you're having troubles, `hdfs` and `start-dfs` are located in `hadoop/bin` and `hadoop/sbin`, respectively. 

Finally, test that Hadoop was correctly installed by checking the Hadoop Distributed File System (HDFS):

``` bash
~$ hadoop fs -ls /
```

If this command doesn't return an error, then we can continue!

## 4. Install Hive

Different releases of Hive can be found [here](https://hive.apache.org/downloads.html), or from the the [Apache Archive](http://archive.apache.org/dist/hive/). I downloaded used Hive 2.3.5 for this example. Be sure to download the binaries, rather than the source. 

``` bash
~$ wget http://archive.apache.org/dist/hive/hive-2.3.5/apache-hive-2.3.5-bin.tar.gz
~$ tar -xvf apache-hive-2.3.5-bin.tar.gz
~$ mv apache-hive-2.3.5-bin.tar.gz hive
```

Add the following to your `.bashrc` and run it with `source`

``` bash
export HIVE_HOME=/home/<USER>/hive
export PATH=$PATH:/home/<USER>/hive/bin
```

Give it a quick test with 

``` bash
~$ hive --version
```

Add the following directories and permissions to HDFS

``` bash
~$ hadoop fs -mkdir -p /user/hive/warehouse
~$ hadoop fs -mkdir -p /tmp
~$ hadoop fs -chmod g+w /user/hive/warehouse
~$ hadoop fs -chmod g+w /tmp
```

Inside `~/hive/conf/`, create/edit `hive-env.sh` and add the following

``` bash
export HADOOP_HOME=/home/<USER>/hadoop
export HADOOP_HEAPSIZE=512
export HIVE_CONF_DIR=/home/<USER>/hive/conf
```

While still in `~/hive/conf`, create/edit `hive-site.xml` and add the following

``` xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:derby:;databaseName=/home/davis/hive/metastore_db;create=true</value>
        <description>JDBC connect string for a JDBC metastore.</description>
    </property>
    <property>
        <name>hive.metastore.warehouse.dir</name>
        <value>/user/hive/warehouse</value>
        <description>location of default database for the warehouse</description>
    </property>
    <property>
        <name>hive.metastore.uris</name>
        <value>thrift://localhost:9083</value>
        <description>Thrift URI for the remote metastore.</description>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionDriverName</name>
        <value>org.apache.derby.jdbc.EmbeddedDriver</value>
        <description>Driver class name for a JDBC metastore</description>
    </property>
    <property>
        <name>javax.jdo.PersistenceManagerFactoryClass</name>
        <value>org.datanucleus.api.jdo.JDOPersistenceManagerFactory</value>
        <description>class implementing the jdo persistence</description>
    </property>
    <property>
        <name>hive.server2.enable.doAs</name>
        <value>false</value>
    </property>
</configuration>
```

(optional) Since Hive and Kafka are running on the same system, you'll get a warning message about some SLF4J logging file. From your Hive home you can just rename the file

``` bash
~/hive$ mv lib/log4j-slf4j-impl-2.6.2.jar lib/log4j-slf4j-impl-2.6.2.jar.bak
```

Now we need to create a database schema for Hive to work with using `schematool`

``` bash
~$ schematool -initSchema -dbType derby
```

Next, enter the Hive shell with the `hive` command

``` bash
~$ hive
...
hive> 
```

Now lets make the database schema for storing our Twitter data. 

``` bash
hive> CREATE TABLE tweets (text STRING, words INT, length INT)
    > ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
    > STORED AS TEXTFILE;
```

You can use `SHOW TABLES;` to double check that the table was created.

## 5. Install Spark

Download from https://spark.apache.org/downloads.html, make sure you choose the option for Hadoop 2.7 or later (unless you used and earlier version). 

Unpack with tar
pip install pyspark
add to bin