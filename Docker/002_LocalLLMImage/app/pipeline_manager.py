import requests
import os
import json
from download_manager_step import DownloadStep

config = "pipeline_download.json"
step_type = "pipeline"

dlstep = DownloadStep(step_type, config)
dlstep.execute()


