## Small Radio Telescope Docs
#### Internal Port Mapping

| Purpose                   | Port  | From      | To                       |
|---------------------------|-------|-----------|--------------------------|
| Status Updates            |  5555 | Daemon    | Dashboard                |
| Command Queue             |  5556 | Dashboard | Daemon                   |
| GNU Radio XMLRPC          |  5557 | Daemon    | GNU Radio                |
| Raw I/Q Data w. Tags      |  5558 | GNU Radio | Daemon, Client (Opt.)    |
| Raw I/Q Data w/o Tags     |  5559 | GNU Radio | Dashboard, Client (Opt.) |
| Processed Spec. Data (Av) |  5560 | GNU Radio | Dashboard, Client (Opt.) |
| Processed Spec. Data (Sum)|  5561 | GNU Radio | Dashboard, Client (Opt.) |
| Dashboard Webpage         |  8080 | Dashboard | Client                   |
