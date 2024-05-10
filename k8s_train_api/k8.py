from google.oauth2 import service_account
from google.cloud.container_v1 import ClusterManagerClient
from kubernetes import client, config
import os
import time 
import datetime
import urllib3
# from firestore import add_job_to_firestore
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# creating a connection with kubernetes cluster
def configure_k8():
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = service_account.Credentials.from_service_account_file('autolabel-287715-bff75ec03073.json', scopes=SCOPES)
    cluster_manager_client = ClusterManagerClient(credentials=credentials)
    cluster = cluster_manager_client.get_cluster('autolabel-287715', 'us-central1-c', 'autolabel-temp')
    configuration = client.Configuration()
    configuration.host = "https://"+cluster.endpoint+":443"
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": "Bearer " + credentials.token}
    client.Configuration.set_default(configuration)
    v1 = client.CoreV1Api()
    batch_v1 = client.BatchV1Api()
    return v1, batch_v1


class KubernetesJobs:
    
    def __init__(self):
        # Configs can be set in Configuration class directly or using helper utility
        self.v1, self.batch_v1 = configure_k8()
            
    # This create a job object 
    def create_job_object(self,name,image,command):
        # Configureate Pod template container
        container1 = client.V1Container(
                name=name,
                image=image,
                command=command)
        container2 = client.V1Container(
                        name='sqlapp',
                        image='gcr.io/cloudsql-docker/gce-proxy:1.17',
                        command=["/cloud_sql_proxy","-instances=labellerrprod:us-central1:labellerr=tcp:3306","-credential_file=/secrets/sql_credentials.json"],
                        volume_mounts=[client.V1VolumeMount(name='my-secrets-volume',mount_path='/secrets/',read_only=True)]
                        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": name,'image':'automl',"process":'labellerr-automl'}),
                spec=client.V1PodSpec(restart_policy="Never", containers=[container1, container2],volumes=[client.V1Volume(name='my-secrets-volume',secret=client.V1SecretVolumeSource(secret_name='cloudsql-instance-credentials'))]))
        # Create the specification of deployment
        # Create the specification of deployment
        spec = client.V1JobSpec(
                template=template,
                backoff_limit=1,
                ttl_seconds_after_finished=5,
                active_deadline_seconds=7200)
        # Instantiate the job object
        job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(name=name),
                spec=spec)
        return job

    # This runs the job object
    def run_job(self,api_instance, job):
        api_response = api_instance.create_namespaced_job(
                    body=job,
                    namespace="default")

    # create training job
    def create_job(self,data):
        command = data['command']
        job_name = data['job_id']
        image = data['docker_uri']
        pods = self.list_pods(job_name)
        flag = False
        for pod in pods:
            if pod['status'] == 'Running' or pod['status'] == 'Pending':
                # there is a running or pending job already
                flag = True
        # if there is no running and pending pod for this job
        # create a new job
        if not flag:
            # first try to delete the job
            # in case failed or succeeded pods are present for this job
            try:
                self.delete_job(job_name)
            except:
                pass
            # After deleting failed or succeeded pods
            # create a new job for this question  
            try:
                job = self.create_job_object(job_name,image,command)
                self.run_job(self.batch_v1,job)
            except Exception as err:
                print('There was error creating this job : ',err)
                return str(err)
        else:
            return 'Job with same id is already running'
        # add_job_to_firestore(data,'train')
        return job_name

    # Delete a job
    def delete_job(self,job_name):
        try:
            api_response = self.batch_v1.delete_namespaced_job(
                name=job_name,
                namespace="default",
                body=client.V1DeleteOptions(
                    propagation_policy='Foreground',
                    grace_period_seconds=0))
            # this sleep is required  deletion of job may take little time
            # If we dont use it and directly create a new job then it gives an error
            # to be on safe side
            time.sleep(2)
            return f'Job {job_name} deletion in progress'
        except Exception as e:
            return 'No job running for deletion'
        
    # List all pods with their current status, name and running time
    def list_pods(self,job_id=None):
        # if job_name is present only get job's pods
        if job_id:
            ret = self.v1.list_namespaced_pod(namespace="default",label_selector=f'app in ({job_id})')
        else:
            ret = self.v1.list_namespaced_pod(namespace="default")
        pods = []
        for i in ret.items:
            finished_at = 0
            termination_reason = 'Not terminated'
            try:
                # if job has been completed or terminated for other reason, only then these value be present
                finished_at = datetime.datetime.timestamp(i.status.container_statuses[0].state.terminated.finished_at)
                termination_reason = i.status.container_statuses[0].state.terminated.reason
            except Exception as err:
                pass
            pods.append({
                'status':i.status.phase,
                'name':i.metadata.name,
                'running_time': (int(time.time()) - int(datetime.datetime.timestamp(i.status.start_time))),
                'start_time':datetime.datetime.timestamp(i.metadata.creation_timestamp),
                'finished_at':finished_at,
                'termination_reason':termination_reason
            })
        return pods
    
    # Get pod's complete status
    def get_job_detailed_status(self,job_name):
        job_pods = self.list_pods(job_name)
                
        if len(job_pods) == 0:
            return None # No running job
        
        # if multiple pods are running in case earlier pod was failed
        # latest one with least running time will be required one
        # getting latest pod
        minimum_time = job_pods[0]['running_time']
        latest_pod = job_pods[0]
        for pod in job_pods:
            if pod['running_time'] < minimum_time:
                minimum_time = pod['running_time']
                latest_pod = pod
        return latest_pod    
    
    # delete all failed and completed jobs pods
    def delete_all_failed_succeeded_pods(self):
        pods = self.list_pods()
        for pod in pods:
            if pod['status'] == 'Succeeded' or pod['status'] == 'Failed':
                self.delete_pod(pod['name'])        
          
    # delete a pod         
    def delete_pod(self,name, namespace='default'):
        delete_options = client.V1DeleteOptions()
        api_response = self.v1.delete_namespaced_pod(
            name=name,
            namespace=namespace,
            body=delete_options)
