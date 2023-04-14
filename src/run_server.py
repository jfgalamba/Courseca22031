import os

def main():
    args = parse_cmdline_args()
    start_uvicorn(args)
#:

def parse_cmdline_args():
    from docopt import docopt
    help_doc = """
FastAPI Web server for the course management Web App.

Usage:
  main.py [-p PORT] [-h HOST_IP] [-r] [-c LEVEL] [-w WORKERS] 

Options:
  -p PORT, --port=PORT            Listen on this port [default: 8000]
  -h HOST_IP, --host=HOST_IP      Listen on this IP address [default: 127.0.0.1]
  -r, --reload                    Reload app
  -w WORKERS, --workers=WORKERS   Number of worker processes
  -c LEVEL, --config-level=LEVEL  Configuration level [default: PROD]
                                        DEV  -> Development
                                        PROD -> Production 
"""
    args = docopt(help_doc)
    os.environ['CONFIG_LEVEL'] = args['--config-level']
    if args['--workers']:
        args['--workers'] = int(args['--workers'])
    return args
#:

def start_uvicorn(cmdline_args: dict):
    import uvicorn
    args = cmdline_args

    uvicorn.run(
        'config_server:app',
        port = int(args['--port']), 
        host = args['--host'],
        reload = args['--reload'],
        workers = args['--workers'],
        reload_includes=[
            '*.pt',
            '*.css',
        ],
    )
#:

if __name__ == '__main__':
    main()

