"""HighThroughputExecutor builds on the Swift/T EMEWS architecture to use MPI for fast task distribution
"""

import logging

try:
    import mpi4py
except ImportError:
    _mpi_enabled = False
else:
    _mpi_enabled = True

from parsl.executors.errors import *
from parsl.executors.high_throughput.htex import HighThroughputExecutor

from parsl.utils import RepresentationMixin
from parsl.providers import LocalProvider

logger = logging.getLogger(__name__)


class ExtremeScaleExecutor(HighThroughputExecutor, RepresentationMixin):
    """Executor designed for leadership class supercomputer scale

    The ExtremeScaleExecutor system has 3 components:
      1. The ExtremeScaleExecutor instance which is run as part of the Parsl script.
      2. The Interchange which is acts as a load-balancging proxy between workers and Parsl
      2. The MPI based fabric which coordinates task execution over several nodes.
      3. ZeroMQ pipes that connect the ExtremeScaleExecutor and the fabric

    Our design assumes that there is a single fabric running over a `block` and that
    there might be several such `fabric` instances.

    Here is a diagram

    .. code:: python


                        |  Data   |  Executor   |  Interchange  | External Process(es)
                        |  Flow   |             |               |
                   Task | Kernel  |             |               |
                 +----->|-------->|------------>|->outgoing_q---|-> mpi_worker_pool
                 |      |         |             | batching      |    |         |
           Parsl<---Fut-|         |             | load-balancing|  result   exception
                     ^  |         |             | watchdogs     |    |         |
                     |  |         |   Q_mngmnt  |               |    V         V
                     |  |         |    Thread<--|-incoming_q<---|--- +---------+
                     |  |         |      |      |               |
                     |  |         |      |      |               |
                     +----update_fut-----+


    Parameters
    ----------

    provider : :class:`~parsl.providers.provider_base.ExecutionProvider`
       Provider to access computation resources. Can be one of :class:`~parsl.providers.aws.aws.EC2Provider`,
        :class:`~parsl.providers.cobalt.cobalt.Cobalt`,
        :class:`~parsl.providers.condor.condor.Condor`,
        :class:`~parsl.providers.googlecloud.googlecloud.GoogleCloud`,
        :class:`~parsl.providers.gridEngine.gridEngine.GridEngine`,
        :class:`~parsl.providers.jetstream.jetstream.Jetstream`,
        :class:`~parsl.providers.local.local.Local`,
        :class:`~parsl.providers.sge.sge.GridEngine`,
        :class:`~parsl.providers.slurm.slurm.Slurm`, or
        :class:`~parsl.providers.torque.torque.Torque`.
    label : str
        Label for this executor instance.
    engine_debug : Bool
        Enables engine debug logging

    public_ip : string
        Please set the public ip of the machine on which Parsl is executing

    worker_ports : (int, int)
        Specify the ports to be used by workers to connect to Parsl. If this option is specified,
        worker_port_range will not be honored.

    worker_port_range : (int, int)
        Worker ports will be chosen between the two integers provided

    internal_port_range : (int, int)
        Port range used by Parsl to communicate with internal services.

    """

    def __init__(self,
                 label='ExtremeScaleExecutor',
                 provider=LocalProvider(),
                 launch_cmd=None,
                 public_ip="127.0.0.1",
                 worker_ports=None,
                 worker_port_range=(54000, 55000),
                 internal_port_range=(55000, 56000),
                 storage_access=None,
                 working_dir=None,
                 engine_debug=False,
                 mock=False,
                 managed=True):

        super().__init__(label=label,
                         provider=provider,
                         launch_cmd=launch_cmd,
                         public_ip=public_ip,
                         worker_ports=worker_ports,
                         worker_port_range=worker_port_range,
                         internal_port_range=internal_port_range,
                         storage_access=storage_access,
                         working_dir=working_dir,
                         engine_debug=engine_debug,
                         mock=mock,
                         managed=managed)

        if not _mpi_enabled:
            raise OptionalModuleMissing("mpi4py", "Cannot initialize ExtremeScaleExecutor without mpi4py")
        else:
            # This is only to stop flake8 from complaining
            logger.debug("MPI version :{}".format(mpi4py.__version__))

        logger.debug("Initializing ExtremeScaleExecutor")

        if not launch_cmd:
            self.launch_cmd = """mpiexec -np {tasks_per_node} mpi_worker_pool.py {debug} --task_url={task_url} --result_url={result_url}"""


if __name__ == "__main__":

    print("Start")
    turb_x = ExtremeScaleExecutor()
    print("Done")
