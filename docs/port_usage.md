## Small Radio Telescope Docs
#### Internal Port Mapping

The SRT control software primarily uses sockets in order to communicate between its various different components.
This gives the user the ability to be able to remotely control or access data (depending on the purpose of the port), just by opening the specific port on the host system.
Excluding the Dashboard Webpage and XMLRPC, all of the ports use the ZeroMQ socket library, and are capable of accepting from multiple simultaneous sources or multiple recipients depending on the purpose of the port.
For instance, if the user were to open up port 5558, anyone could subscribe to the ZMQ publisher socket and receive a live stream copy of the raw I/Q samples from the SDR along with GNU Radio metadata data tags.  Similarly, opening up port 5559 would let anyone subscribe for a copy of the raw I/Q samples that don't contain any GNU Radio metadata, which means the received bytes can just be cast into their appropriate complex float datatype without the need for GNU Radio to parse it.

Quick descriptions of each port, its intended purpose in the system, and the original source and destination of the data are listed below:


| Purpose                   | Port  | From      | To              |
|---------------------------|-------|-----------|-----------------|
| Status Updates            |  5555 | Daemon    | Dashboard       |
| Command Queue             |  5556 | Dashboard | Daemon          |
| GNU Radio XMLRPC          |  5557 | Daemon    | GNU Radio       |
| Raw I/Q Data w. Tags      |  5558 | GNU Radio | Daemon          |
| Raw I/Q Data w/o Tags     |  5559 | GNU Radio | Dashboard       |
| Raw Spec. w. Tags         |  5560 | GNU Radio | User (Opt.)     |
| Raw Spec. w/o Tags        |  5561 | GNU Radio | Dashboard       |
| Calibrated Spec. w. Tags  |  5562 | GNU Radio | Daemon          |
| Calibrated Spec. w/o Tags |  5563 | GNU Radio | Dashboard       |
| Dashboard Webpage         |  8080 | Dashboard | User            |

Note: User (Opt.) indicates a port where there is no intended destination unless the user optionally wishes to listen to that port with a GNU Radio ZMQ Sub Source.
