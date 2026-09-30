"""python -m sales_agent.hrl.train --steps 20000 --episodes 100"""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from .environments import CustomerGym, VoiceGym, PERSONAS
from .state import rule_action, Strategy, OBS_SIZE
from .policy import voice_rule

def evaluate(factory, choose, episodes, seed):
    rows=[]
    for n in range(episodes):
        env=factory(); obs,_=env.reset(seed=seed+n); reward=0
        while True:
            obs,r,done,truncated,info=env.step(int(choose(obs)));reward+=r
            if done or truncated:break
        rows.append({'reward':reward,**{k:float(v) for k,v in info.items() if isinstance(v,(bool,int,float))}})
    result={k:float(np.mean([r[k] for r in rows])) for k in rows[0]}
    result['reward_standard_error']=float(np.std([r['reward'] for r in rows])/np.sqrt(episodes))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=20000);p.add_argument('--episodes',type=int,default=100)
    p.add_argument('--seed',type=int,default=42);p.add_argument('--output',default='artifacts/hrl');p.add_argument('--llm-baseline',action='store_true');args=p.parse_args()
    if args.steps<256 or args.episodes<1:p.error('steps must be >=256 and episodes >=1')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(1);np.random.seed(args.seed);torch.manual_seed(args.seed)
    models={}
    for name,env in [('strategy',CustomerGym()),('voice',VoiceGym()),('strategy_no_information',CustomerGym(information_reward=False))]:
        check_env(env)
        model=PPO('MlpPolicy',Monitor(env,str(out/name)),n_steps=256,batch_size=64,n_epochs=5,
                  policy_kwargs={'net_arch':[64,64]},device='cpu',seed=args.seed,verbose=0)
        model.learn(args.steps);model.save(out/name);models[name]=model
        print(f'Trained {name}: {model.num_timesteps} steps',flush=True)
    # Behavior cloning baseline uses only rule-labelled training trajectories.
    samples=[];labels=[];env=CustomerGym()
    for i in range(100):
        obs,_=env.reset(seed=args.seed+i)
        for _ in range(20):
            a=int(rule_action(obs));samples.append(obs.copy());labels.append(a)
            obs,_,done,trunc,_=env.step(a)
            if done or trunc:break
    supervised=torch.nn.Sequential(torch.nn.Linear(OBS_SIZE,64),torch.nn.Tanh(),torch.nn.Linear(64,len(Strategy)))
    optimizer=torch.optim.Adam(supervised.parameters(),lr=.01)
    x=torch.tensor(np.array(samples));y=torch.tensor(labels)
    for _ in range(150):
        loss=torch.nn.functional.cross_entropy(supervised(x),y);optimizer.zero_grad();loss.backward();optimizer.step()
    torch.save(supervised.state_dict(),out/'supervised.pt')
    rng=np.random.default_rng(args.seed)
    report={'scope':'Synthetic simulator only; not evidence of real customer conversion or real audio quality.',
            'seed':args.seed,'steps':args.steps,'episodes_per_split':args.episodes,'personas':PERSONAS,
            'llm_baseline':{'status':'not_run','reason':'Requires a configured hosted LLM and separate evaluation budget'},'strategy':{}}
    for split in ['validation','test']:
        report['strategy'][split]={}
        policies={'random':lambda o:rng.integers(len(Strategy)),'rules':rule_action,
                  'supervised':lambda o:int(supervised(torch.tensor(o)).argmax()),
                  'ppo':lambda o:models['strategy'].predict(o,deterministic=True)[0],
                  'ppo_no_information':lambda o:models['strategy_no_information'].predict(o,deterministic=True)[0]}
        if args.llm_baseline:
            from .llm_baseline import LLMBaseline
            policies['llm']=LLMBaseline()
            report['llm_baseline']={'status':'run','model':policies['llm'].model}
        for name,choose in policies.items():
            report['strategy'][split][name]=evaluate(lambda:CustomerGym(split),choose,args.episodes,100000 if split=='test' else 50000)
    report['voice']={name:evaluate(VoiceGym,choose,args.episodes,200000) for name,choose in {
        'fixed_rules':voice_rule,'ppo':lambda o:models['voice'].predict(o,deterministic=True)[0]}.items()}
    rule_test=report['strategy']['test']['rules'];ppo_test=report['strategy']['test']['ppo']
    report['promotion']={
        'promote_strategy_ppo':bool(ppo_test['success']>=rule_test['success']+.05 and ppo_test['reward']>=rule_test['reward']),
        'criteria':'At least +5 percentage points held-out synthetic success and no lower mean reward than rules.',
        'decision':'Use PPO' if ppo_test['success']>=rule_test['success']+.05 and ppo_test['reward']>=rule_test['reward'] else 'Keep rule baseline'}
    fixed=report['voice']['fixed_rules'];voice_ppo=report['voice']['ppo']
    report['promotion']['promote_voice_ppo']=bool(voice_ppo['reward']>fixed['reward'] and voice_ppo['interruptions']<=fixed['interruptions'])
    (out/'evaluation.json').write_text(json.dumps(report,indent=2))
    from .report import reward_curves
    reward_curves(out)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
