import argparse
import json
from .report import ROOT,run,save


def main():
    parser=argparse.ArgumentParser(description='Synthetic marketing decision engine')
    parser.add_argument('command',choices=['demo','serve'],nargs='?',default='demo')
    parser.add_argument('--port',type=int,default=8010)
    parser.add_argument('--budget',type=float)
    args=parser.parse_args()
    if args.command=='serve':
        from .server import serve
        serve(args.port)
    else:
        report=run(budget=args.budget);save(report,ROOT/'reports')
        print(json.dumps({'evaluation':{k:v for k,v in report['evaluation'].items()
                                      if k not in ['predictions','actual','baseline_predictions']},
                          'modelled_change_percent':report['plan']['modelled_change_percent'],
                          'outputs':str(ROOT/'reports')},indent=2))


if __name__=='__main__':main()
