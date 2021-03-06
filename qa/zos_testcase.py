import os
import json
import unittest
import subprocess
from jumpscale import j
from netaddr import valid_ipv4
from configparser import ConfigParser

def run_cmd(cmd):
    subprocess.run([cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

class SimpleTest(unittest.TestCase):

    """
    test cases to test using ZOS with virtualbaox instance 
    """
    @classmethod
    def setUpClass(cls):
        """
        create VM instance and then create containers on top of it 
        """
        default_init = run_cmd("./zos init --name=default_init --port=12345 --reset")
        default_init_1 = run_cmd("./zos init --name=default_init_1 --port=12345 --reset")

    def setUp(self):
        pass

    def test_setdefault():
        """
        check if certain node is used as default or not
        """
        set_default = run_cmd("./zos setdefault default_init")
        # check if the default_init node is used as default or not
        parser = ConfigParser()
        parser.read("~/.config/zos.toml")
        node = parser.get('app', 'defaultzos')
        assertEqual(node,'default_init' , msg = "default_init node isn't set as default")

    def test_ping(self):
        """
        test zos ping command 
        
        ./zos ping            
            "PONG Version: development @Revision: ffe97313ef00b018d3d66e3343d68fa107217df5"
        """
        ping = subprocess.run(["./zos ping"], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        testping = ping.stdout.decode()
        self.assertIn("PONG",testping, msg="the node isn't pingable")

    def test_showconfig(self):
        """
            test showconfig command 
        """
        showconfig = run_cmd("./zos showconfig")
        output = showconfig.stdout.decode()
        self.assertIn("defaultzos", output, msg="showconfig command isn't working correctly")

    def test_showactive(self):
        """
            test showactive command
        """
        showactive = run_cmd("./zos showactive")
        output = showactive.stdout.decode()
        self.assertIn("default_init", output, msg="default_init node is an active node")

    def test_showactiveconfig(self):
        showactiveconfig = run_cmd("./zos showactiveconfig") 
        output_showactiveconfig = json.loads(showactiveconfig.stdout.decode())
        # need to check if the output contains (address, isvbox, port)
        self.assertIn("address", output_showactiveconfig, msg="wrong output the command should contain address part")
        self.assertIn("port", output_showactiveconfig, msg="wrong output the command should contain port part")
        self.assertIn("isvbox", output_showactiveconfig, msg="wrong output the command should contain isvbox part")

    def test_create_container(): 
        """
            test create container 
            connect to vm instance remotely using js9 client and check the new created vms 
        """
        container1 = run_cmd("./zos container new --name=container1 --root=https://hub.grid.tf/thabet/redis.flist")
        container2 = run_cmd("./zos container new --name=container2")
        test_con = j.clients.zos.get('test', data={'host':'127.0.0.1', 'port':'12345'})
        con_list = test_con.containers.list()
        self.assertIn("container1", con_list, msg="first container isn't created correctly") 
        self.assertIn("container2", con_list, msg="second container isn't created correctly")

    def test_containers_list(self):     
        """
            test list containers
        """
        container_list = run_cmd("./zos container list --json")
        output_container_list = json.loads(container_list.stdout.decode())
        self.assertIn("id", output_container_list, msg="container list output should contain id part")
        self.assertIn("cpu", output_container_list, msg="container list output should contain cpu part")
        self.assertIn("root", output_container_list, msg="container list output should contain root part")
        self.assertIn("storage", output_container_list, msg="container list output should contain storage part")
        self.assertIn("pid", output_container_list, msg="container list output should contain pid part")
        self.assertIn("ports", output_container_list, msg="container list output should contain ports part")
    
    def test_container_sshinfo(self):
        """
            show ssh info for certain container
        """
        container_ssh_info = run_cmd("./zos container sshenable")
        # check if it starts with root word
        username = container_ssh_info.stdout.decode().split("\n")[6].startswith("root")  
        self.assertTrue(username, True, msg=None)
        ip = container_ssh_info.stdout.decode().split("\n")[6].split(" ")[0].split("@")[1]
        ip_check = valid_ipv4(ip)
        self.assertTrue(ip_check, True, msg=None)

    def file_upload(self):
        """
            function to test upload for files to certain continer
        """
        # create file to test upload function
        file_test = os.system('touch /tmp/test') 
        file_upload_file = run_cmd("./zos container upload /tmp/test /tmp/")
        # check if the file is uploaded correctly or not using zos exec command line
        #############################################################################

    def container_mount(self):
        """
            test mount command 
        """
        os.system("mkdir /tmp/testmount")
        test_container_mount = run_cmd("./zos container mount / /tmp/testmount")
        test_mount = os.path.ismount("/tmp/testmount")
        self.assertTrue(test_mount, msg="mount point isn't set true")

    def container_delete(self):
        """
            test delete container function
        """
        # delete the last container (container 3) which i just created
        delete_container = run_cmd("./zos container delete")
        # check the list of containers on vm instance node
        test_con = j.clients.zos.get('test', data={'host':'127.0.0.1', 'port':'12345'})     
        con_list = test_con.containers.list()
        self.assertIn("container2", con_list, msg="second container isn't deleted correctly")
        
    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        # delete the vm instance
        default_init_remove = run_cmd("zos remove --name=default_init")
        default_init_1_remove = run_cmd("zos remove --name=default_init_1")
        
    if __name__ == '__main__':
        unittest.main()
