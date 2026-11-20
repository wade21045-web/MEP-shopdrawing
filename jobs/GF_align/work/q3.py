import pickle,collections
R=pickle.load(open('result.pkl','rb'))
print(collections.Counter((i.get('zone'),i.get('result')) for i in R['ISS']) if isinstance(R['ISS'][0],dict) else R['ISS'][0])
