# LEON_BCS
some code for aliyun BCS

# Brief Description:
1. config.py contains args for bcs connect,deadline connect,release conditions.  
2. bcs_create.py used for creating bcs cluster and starting instances. After success started，create deadline pool that user customed and add instance to this pool.  
3. deadline_func.py contains some deadline func.  
4. bcs_release.py offers two release methods: First,release according deadline slave stat; Second,release according cpu&ram use ratio. User can custom RELEASE_TIME_MINUTE for each cluster, instance will be released after RELEASE_TIME_MINUTE.  
note that a precondition for cpu&ram releasing is a common administrator account in your custom image. This account is used for remote getting cpu&ram use ratio.  
