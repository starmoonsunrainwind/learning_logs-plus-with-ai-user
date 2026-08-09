from django.shortcuts import render,redirect,get_object_or_404

# Create your views here.
from .models import Topic,Entry,Comment
from .forms import TopicForm,EntryForm,CommentForm
from django.contrib.auth.decorators import login_required
from django.http import Http404
def index(request):
    #学习笔记的主页
    return render(request,'learning_logs/index.html')

def topics(request):
    #显示所有的主题
    context={}
    if request.user.is_authenticated:
        my_topics = Topic.objects.filter(owner=request.user).order_by('-date_added')
        public_topics=Topic.objects.exclude(owner=request.user).filter(public=True).order_by('-date_added')
        context={'my_topics':my_topics,'public_topics':public_topics}
    else:
        public_topics = Topic.objects.filter(public=True).order_by('-date_added')
        context = {'public_topics':public_topics}
    return render(request, 'learning_logs/topics.html',context)

def topic(request,topic_id):
    #显示单个主题及所有条目
    topic = get_object_or_404(Topic,id=topic_id)
    if topic.public:
        pass
    else:
        if topic.owner != request.user:
            raise Http404
    entries = topic.entry_set.order_by('-date_added')
    if request.method == 'POST' and 'comment_submit' in request.POST:
        form=CommentForm(data=request.POST)
        if form.is_valid:
            if topic.public:
                new_comment = form.save(commit=False)
                new_comment.entry_id = request.POST.get('entry_id')
                new_comment.owner = request.user
                new_comment.save()
                return redirect('learning_logs:topic',topic_id=topic_id)
    else:
        form=CommentForm()
    context = {'topic':topic,'entries':entries,'form':form}
    return render(request,'learning_logs/topic.html',context)
@login_required
def new_topic(request):
    #添加新主题
    if request.method != 'POST':
        #未提交数据：创建新表单
        form = TopicForm()
    else:
        #POST提交的数据：对数据进行处理
        form = TopicForm(data=request.POST)
        if form.is_valid():
            new_topic = form.save(commit=False)
            new_topic.owner=request.user
            new_topic.save()
            return redirect('learning_logs:topics')
    #显示空表单或指出表单数据无效
    context = {'form':form}
    return render(request,'learning_logs/new_topic.html',context)
@login_required
def new_entry(request,topic_id):
    #在特定主题中添加新条目
    topic = Topic.objects.get(id=topic_id)
    if topic.owner != request.user:
        raise Http404
    if request.method != 'POST':
        form = EntryForm()
    else:
        form=EntryForm(data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.topic=topic
            new_entry.save()
            return redirect('learning_logs:topic',topic_id=topic_id)
    context = {'topic':topic,'form':form}
    return render(request,'learning_logs/new_entry.html',context)
@login_required
def edit_entry(request,entry_id):
    """编辑既有的条目"""
    entry=Entry.objects.get(id=entry_id)
    topic=entry.topic
    if topic.owner != request.user:
        raise Http404
    if request.method != 'POST':
        form=EntryForm(instance=entry)
    else:
        form = EntryForm(instance=entry,data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('learning_logs:topic',topic_id=topic.id)
    context={'entry':entry,'topic':topic,'form':form}
    return render(request,'learning_logs/edit_entry.html',context)
@login_required
def edit_topic(request,topic_id):
    topic=get_object_or_404(Topic,id=topic_id)
    if topic.owner !=request.user:
        raise Http404
    if request.method !='POST':
        form = TopicForm(instance=topic)
    else:
        form = TopicForm(instance=topic,data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('learning_logs:topic',topic_id=topic.id)
    context = {'topic':topic,'form':form}
    return render(request,'learning_logs/edit_topic.html',context)
def ai_personas(request):
    return render(request,'learning_logs/ai_personas.html')
    
    