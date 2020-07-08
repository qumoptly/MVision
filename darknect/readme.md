# 深度学习框架  人工智能操作系统 训练&前向推理

OneFlow & 清华计图Jittor & 华为深度学习框架MindSpore & 旷视深度学习框架MegEngine(天元） & caffe & Google的TFBOYS & Facebook的Pytorch  & XLA

严格意义来说TVM和Jittor都不算深度学习框架，TVM和Jittor更多的是一套独立的深度学习编译器。我们可以将导出的模型文件通过TVM或者Jittor离线编译成一个Serving的模块，从而可以在云上或者端上部署模型的预测服务。

[华为 mindspore](https://github.com/Ewenwan/mindspore)

[清华计图Jittor  gt](https://github.com/Jittor/jittor/blob/master/README.cn.md)

依赖: sudo apt install python3.7-dev libomp-dev    pip3 install pybind11  numpy   tqdm    pillow  astunparse  six  wheel

pybind11使用问题  https://zhuanlan.zhihu.com/p/52619334 

[旷视深度学习框架MegEngine gt](https://github.com/MegEngine/MegEngine)

[模型可视化超好用的工具](https://github.com/lutzroeder/Netron)

[使用自动代码生成技术TVM优化深度学习算子的一些思考](https://zhuanlan.zhihu.com/p/101026192)

[基于ARM-v8的Tengine GEMM教程](https://github.com/Ewenwan/Tengine_gemm_tutorial)


## 深度学习编译器

[谈谈对深度学习编译技术的一些思考](https://zhuanlan.zhihu.com/p/87458316)

深度学习编译器，一般是分两阶段优化，一个是high level optimization, 譬如在XLA里叫HLO， 这部分做硬件无关优化； 还有一个阶段是代码生成阶段，即codegen，和硬件体系结构相关。不同的编译器在这俩阶段的处理上各有所长。第一阶段的问题基本上被解决了，难的是第二阶段。

深度学习编译器的价值取决于AI芯片的前途。AI芯片上开发编译器的难度不高，基本上和在GPU上调用cublas, cudnn写程序差不多，因为基本的张量运算都用专用电路固化了，没啥可优化的（当然访存和计算做流水还是要做的），为某款AI芯片研发深度学习编译器，可能只需要关注第一阶段的问题(HLO)，不需要解决第二阶段的问题(codegen)。如果对专用芯片上代码怎么写感兴趣，**可参照Glow, 它提供了一个为Habana 后端，这可能是唯一一个开源的AI芯片代码示例。**

深度学习编译器的命运与AI芯片竞争格局息息相关，但我们并没有讨论AI芯片未来如何，这是另一个问题了，真正投入搞AI芯片的玩家对这个问题想的更清楚。

1、前端用DSL还是限定一个算子集合。XLA没有DSL,而是限定了一些基本算子，element-wise, map, reduce, broadcast, matmul 等等，蛮像函数式编程里面那些基本运算，用这些基本算子可以搭建起来tensorflow 里绝大多数更上层的算子，譬如batchnorm, softmax等。这么做当然限制了表示能力，但却给第二阶段codegen 带来极大便利，因为它只需要为这些限定的算子emit LLVM IR, 用固定的套路即可，相当于逃避了第二阶段优化那个难题。Glow实际上采用了和XLA相似的策略，对于第二步取了个巧，对于常见的矩阵运算算子提供了代码生成的模板，用模板并不意味着对不同的参数（譬如矩阵的长宽）都生成一样的代码。模板里面的参数是可调的，这样如果输入代码超参数不同，它也会针对不同的超参数做一些对应的优化。所以对于XLA和Glow可观赏的只有HLO这一层，这也是比较务实的做法，因为第二阶段优化太难了。**TVM，TC, Tiramisu, PlaidML使用了DSL**，这使得它们能表示的运算范围更广，当然也直面了第二阶段优化的挑战，这也是这些编译器出彩的地方，我们在下一个要点里讨论第二阶段优化。对第一阶段优化来说，XLA做的相当全面了，可能是最全面的。

2，剑宗还是气宗？在特定体系结构上自动生成最优代码，可以看出有俩套路，一个套路可以称之为剑宗，也好似一种自底向上的办法，即把专家手工优化代码的经验提炼出来，形成一些粗线条的rule（规则）, 这是TVM的路线，也就是来自Halide的思路，那些rule称为schedule，Halide的最重要贡献是提出了问题表示方法，但没有解决自动化这个问题，当然自动化问题很困难。还有一个套路可称之为气宗，寻求一种高层次的数学抽象来描述和求解代码生成问题，这个代表就是TC, Tiramisu, MLIR等依赖的Polyhedral method（多面体方法）。

**深度学习编译器和传统编译器技术很不相同，它只解决一类特定问题，不去解决控制流问题，基本上是解决多重循环优化，也就是稠密计算问题。**

Polyhedral method 是一种对多重循环程序的表示方法，问题表示出来之后，并不一定要借助isl求解。isl是什么？对一个比较复杂的cost model, 一个polyhedral 表示的计算，生成什么样的代码最优？这是一个离散解空间上的组合优化问题，有时可描述成整数线性规划，isl (integer set library)就是来求解这个问题的一个开源库。像TC， Tiramisu 用了isl, PlaidML和MLIR仅仅用了多面体表示却没有借助isl, 猜测：问题搜索空间太大时，isl 也不行。多面体方法只解决表示问题，不解决自动化问题。

用多面体与否实际上和前端是否用DSL也有关，用Polyhedral 的都用DSL, 表明多面体的表达能力和能求解的问题范围非常广，用DSL但不用Polyhedral 也有，譬如Halide, TVM, Tiramisu 作者对Halide表达能力有所批评，需要注意的是， Halide和Tiramisu 作者们其实是同一位MIT教授的学生，这是自己对自己的批评。

polyhedral 是近些年发展出来的最优雅的抽象方法，是并行编译领域的一种数学抽象，利用空间几何的仿射变换来实现循环优化。

Pluto是众多Polyhedral编译器中应用范围最广、最成功的编译器之一，以该编译器为平台实现的Pluto调度算法代表了Polyhedral model调度最先进的研究水平。Pluto编译器是一个很好的开发程序并行性和数据局部性的优化工具。

Pluto调度算法至今在众多领域包括将机器学习算法部署在特定加速部件等方面都发挥着重要作用。所以，Pluto编译器是一个很好的循环优化工具，也是研究Polyhedral model一个很好的平台。 Pluto编译器是一个从C程序到OpenMP的source-to-source编译器。

polyhedral compilation的研究内容分为依赖关系分析、调度变换和代码生成几个部分。当然，在做这些之前，polyhedral需要用一个parser来做解析，现在比较常用的parser是pet（“Polyhedral extraction tool”（IMPACT 2012））还有clan。polyhedral涉及到的工具及其链接大部分可以在polyhedral.info这个网站上找到。

现在的polyhedral研究大多被认为是由Feautrier针对数据流分析的工作“Dataflow analysis of array and scalar references”（IJPP 1991）奠基而来的。数据流分析的优势在于把依赖关系分析的粒度从语句细化到语句的实例，所以结果比传统的依赖关系分析结果更精确。但是在polyhedral里面的依赖关系分析，我并不会推荐去读这篇文章，因为这篇文章 比较难懂，我更推荐去看Pugh的“The Omega test: a fast and practical integer programming algorithm for dependence analysis”（ICS 1991）这篇文章，这篇文章对polyhedral的思维构建很有帮助。

依赖关系分为value-based和memory-based两种依赖关系，这个为polyhedral里面的scheduling算法在优化和正确性方面提供了很多支持。

现在大部分的polyhedral算法是Bondhugula的pluto算法“A practical automatic polyhedral parallelizer and locality optimizer”（PLDI 2008），这个算法是真正让polyhedral前后贯通的一个scheduling算法。如果对scheduling算法感兴趣，我会建议去阅读pluto算法或者Bondhugula的博士论文“Effective Automatic Parallelization and Locality Optimization using the Polyhedral Model”，这个算法也是Pluto编译器的核心。Bondhugula对scheduling算法后续做了许多优化和提升例如Pluto+，这部分可以参考他的个人主页。

polyhedral的代码生成工具主要有CodeGen+，“Code generation for multiple mappings”（Frontiers 1995）和CLooG，“Code generation in the polyhedral model is easier than you think”（PACT 2004）两个工具。CodeGen+部分主要是在Omega库里使用，而CLooG和CodeGen+的代码生成方式有一些不同。这两篇文章都值得去看一下，了解一下如何生成代码。不过，“Polyhedral AST generation is more than scanning polyhedra”（TOPLAS 2015）这篇文章我建议对AST生成部分有兴趣的话可以仔细阅读一下，这个长达50页的文章系统地介绍了如何生成循环的边界、控制流条件语句还有避免代码膨胀等问题。



> **深度学习编译优化技术与手工优化的对比**

深度学习编译优化与手工优化并不是互斥关系，而是互补关系。在一个完整的系统里，应该既有深度学习编译优化，也有手工优化，让各自解决其适合解的问题。

1). 编译优化适合解决给定策略，涉及较多routine性质tedious work的问题。比如我们知道loop unrolling会可能带来性能收益是一个策略问题，但是按什么样的strides来unroll，是一个trial-and error的问题。以及我们都知道对于GEMM进行分tile计算可以提升计算访存比，这是一个策略问题，但是给定一款硬件，按什么尺寸，在什么维度上分tile则是一个trial-and-error的问题。这类问题，适合采取编译优化的手段来解，也往往是编译优化能够在生产效率上显著优于手工优化的地方；

2). 手工优化适合那种不容易精确形式化描述成一个清晰策略，带有一定非逻辑思维的直觉性质（由我们认识规律的能力水平决定）的问题，往往涉及到全局性质优化的问题具备这种性质。比如最近我们针对TensorCore在进行手工优化，会在访存pattern上进行精细的优化，以期最大可能将计算与访存overlap，就会发现涉及到精细的访存排布，至少基于目前我们对TVM schedule描述的理解，如果只是基于TVM显式提供的schedule，不去手写TVM IR，是不容易表达出来的。实际上TVM在设计上提供了Tensorize/intrinsics的接口，也是在一定程度上需要将手工优化的经验嵌入到优化流程里，但也并不是所有的手工优化都可以基于目前的tensorize/intrinsics机制来完成扩充的。

3).手工优化是可能向编译优化迁移的。比如通过扩展编译引擎的内核，来加入对应的支持。比如我们最近在TVM社区里针对NV GPU TensorCore提供了基于graph/IR pass/codegen模块改造的作法，能够做到用户完全无感，自动完成TensorCore kernel优化生成的效果，而社区的另一个相关工作作法则是需要显式提供TensorCore相关intrinsics的描述，将一部分工作offload到用户层。这算是一个手工优化，向编译优化层次迁移的示例。

4).总会有些优化在编译优化层面完成会存在事倍功半的效果，这类优化我们就应该考虑either是通过手工优化扩充，或是通过提供pre-defined library，甚至runtime强化的方式来进行协同优化，而不是什么优化都往编译层面压。反过来也一样。手工优化可以在极限场景下找到非常精细的性能优化空间，但是并不是所有的手工优化所探索的性能空间都复杂精细到编译优化不能支持的程度。找到不同技术适合的土壤就好。之前跟NV的同学沟通，他们针对TensorCore kernel的支持，考虑采取设计若干个小的recipe，recipe提供可定制的可能，再进行拼装组合来实现不同尺寸的GEMM kernel，这种作法，包括CUTLASS的设计思想，在我看来，都具备了一定的将手工优化的经验向编译优化层次转移的味道，只是程度不同而已。

对于AI芯片来说，已经以后专门的硬件架构来解决ai中常见的计算密集型算子，GPU虽然有一定通用性没有完全硬件化，但TensorCore的出现也使它未来可能有这方面的趋势，这样来说软件编译器在这里能做的事情应该是有限的；可能“主要开销都不是计算密集型算子”，数据搬运非常关键。


## 深度学习框架简述

深度学习框架发展到今天，目前在架构上大体已经基本上成熟并且逐渐趋同。无论是国外的Tensorflow、PyTorch，亦或是国内最近开源的MegEngine、MindSpore，目前基本上都是支持EagerMode和GraphMode两种模式。

> Tensorflow

Google的Tensorflow最早是按照GraphMode来设计的，GraphMode是系统同学比较偏爱的一个架构。用户通过申明式的API来定义好模型，然后后面具体的优化、执行都交给后端的系统。由于系统能够一次能够拿到整个执行的Graph，因此系统同学便有足够的空间对系统做各种优化。比如在Tensorflow里面，我们可以做各种类型的优化，包括Placement的优化、图优化（Grappler）、内存优化、分布式优化等。不过GraphMode有一个弊端，就是模型调试。许多使用Tensorflow的算法同学对于运行过程中遇到的各种千奇百怪的问题都感到束手无策。不过需要说的是，从Tensorflow上来看的话Google在整个AI系统领域的布局是最完善的，从底层的芯片（推理、训练、端）、到深度学习框架（Tensorflow、、XLA），再到模型部署（TF Serving、TFLite），最后再到TF的训练链路（TFX、TF.js、Tensorboard、federated）。从这些布局来看，整个Tensorflow的设计完全体现出了Google的系统深度，并完全引领了整个AI系统。

> PyTorch

PyTorch从一开始就是按照EagerMode来进行架构实现。和Tensorflow v1.0对比，PyTorch非常灵活，对于开发者极其友好。因此，在开发者社区上PyTorch很快就逼近了Tensorflow，从最近两年的论文应用上我们也能看到PyTorch的引用数和Tensorflow越来越接近。从这个角度来看会给人一个感觉就是Tensorflow起了个大早赶了个晚集。我们也能看到Tensorflow也在2.0里面也开始支持EagerMode并将EagerMode设置为默认的运行模式，希望能够补齐易用性这个短板。不过其实对于Tensorflow而言转型支持EagerMode其实不容易。就像前面说道的，Tensorflow自身的架构是完全按照GraphMode来设计的，因此为了支持EagerMode，Tensorflow自身的改动也是很痛苦，从Tensorflow的代码来看许多地方都加入了if（eager_mode)这样的判断条件。不过PyTorch也不是完美无缺。对于PyTorch的开发者而言，PyTorch模型的Deployment过程是一个痛苦的过程。这也是在工业界Tensorflow相比较PyTorch更受欢迎的一个重要原因。

> 华为MindSpore

华为在国内是一个很值得尊敬的企业。可以这么说，华为在IT这个领域是整体上部署最完善的公司。这些领域包括了云计算最底层的网络、存储、服务器、芯片，也包括了上层的编译器、高斯数据库。在深度学习这个领域，华为可以说布局也比较完整，比如Asend芯片（训练、推理）、最近刚开源的深度学习框架MindSpore。对于一家企业而言，布局这些领域都是需要极大的决心。不过企业布局这些领域也不是为了开发而开发，为了自研而自研。对于企业而言，布局这些领域最终肯定是希望能够在商业上带来相应的回报。(开源社区与华为共成长)

从MindSpore这个框架的架构来看，MindSpore的架构和目前已有引擎的架构比较相似，整体执行也都是基于自动微分进行的设计。这个也比较合理。另外，整个框架从上往下依次是Python的DSL层、中间的Graph优化层以及底下的执行层。这个架构也是目前主流的引擎的相似的架构。此外，由于有了后发的优势，MindSpore应该是在设计之初就考虑了如何兼具EagerMode和GraphMode两种执行方式，这样就可以同时兼具易用性和高性能。在底层不同设备的支持上，我们也能够看到MindSpore支持了包括CPU，GPU加速器，当然最重要的还是自家的Ascend芯片。

> 自动并行 Auto Parallel

MindSpore里面我觉得一个比较大的亮点也是他们在文档里面强调的一个就是自动并行的训练能力。自动并行是一个在其他领域研究的比较多的方向，比如在大数据领域对于用户写的一条SQL语句我们能够在优化器内部自动生成一个相对较优的执行计划，从而生成一个自动并行的Mapper-Reduce任务。在深度学习这个领域也存在这个问题，那就是如何将用户的模型最大高效的并行执行。

在深度学习这个领域存在多种并行的范式，比如数据并行（Data Paralle)，模型并行（Model Parallel），混合并行（Hybrid Parallel)等。目前在深度学习分布式执行这个领域应用最多的还是数据并行，也就是Data Parallel。业内多个框架，比如Horovod，Tensorflow的DistributeStrategy，PyTorch的DDP，这些都是数据并行的分布式框架。数据并行就是将模型在多个设备上进行复制并行训练，同时基于NCCL进行梯度同步，从而达到分布式执行的效果。数据并行这个架构比较简洁，模型构建也比较清晰，因此目前绝大部分任务都是采用数据并行的训练方式。

MindSpore里面也支持基本的数据并行能力。不过从MindSpore里面他着重强调的是自动并行。这里的自动并行是指从众多的并行可能性里面搜寻出一种最优的并行执行方式，比如将部分算子进行自动拆分从而达到一个比较好的并行效果。从下面的图里面我们能够看到MindSpore的自动并行是基于一个Cost Model来进行并行策略的评估。通过Cost Model，我们可以对不同的并行策略进行评估，从而可以选择一个cost最小的并行策略。在Cost Model里面，我们通常会对通信的cost、计算的cost、算子拆分的cost等进行评估。并行策略的搜寻算法在MindSpore里面我们看到使用了动态规划（dynamic programming)和递归算法(recursive programming)。

> 自动并行的挑战

对于自动并行而言，最大的挑战是如何寻优到最佳的并行策略。对于常见的数据并行而言，我们只需要将模型副本分布到不同的设备上，选择合适的时间对梯度进行AllReduce即可。对于自动并行，我们需要考虑不同的通信拓扑（比如以太网、NVLink、多网卡设备）、算子拆分（Layer间拆分、Layer内拆分）、设备算力、流水并行、算子计算依赖、显存大小、通信成本（Weight，Activation等）等众多维度。Google有一个项目，Mesh-Tensorflow，目前是提供了相应算子的拆分机制。算法同学可以自由的在不同的维度（Batch维度、NCHW四个维度、Matmul维度等）进行拆分。在MindSpore里面我们也看到也提供了类似的拆分能力，在MindSpore源代码里面我们看到了支持算子的定义，不过相应拆分的能力目前没有看到可以让用户来指定。

# 开发深度学习框架的知识架构

1，熟悉常见深度学习模型，CNN, GAN, RNN/LSTM, BERT, Transformer;

2,熟悉后向误差传播算法（BP），完成从标量求导到矩阵求导思维方式的转换，熟悉常见算子的梯度推导（矩阵乘，卷积， 池化，Relu，如果会batch normalization 就一步到位了）；

3，熟悉autograd的基本原理，能自己手撸一个最好；

4，熟悉cuda编程（举一反三），熟悉cuda高阶用法，event, stream, 异步/同步，会优化常见cuda kernel, element-wise, reduce, broadcast， MatMul, conv, pooling 等；

5，熟悉c++和python, 对c++高级用法感到舒服，各种模式，惯用法，模板；熟悉vim, gdb 程序调试；

6，熟悉socket, RDMA编程，熟悉常见collective operation代价分析，譬如ring allreduce, tree allreduce 代价分析；

7，熟悉多线程编程，熟悉锁，条件变量，内核线程，用户级线程，对actor, CSP(coroutine)各种技术熟悉；

8，熟悉编译器基本原理，parser什么的不重要，主要是dataflow分析，灵活运用；熟悉多重循环程序优化技巧，譬如polyhedral 模型；

9，熟悉常见分布式系统原理，mapreduce, spark, flink, tensorflow 等；

10，熟悉计算机体系机构，量化分析方法，Amdahl' Law, Roofline Model, 流水线分析（譬如David Patterson 那本书）；

11，熟悉操作系统原理及常用系统诊断工具，譬如各种资源利用率分析；

12，programming language 原理，命令式编程，函数式编程，逻辑编程，入门书《程序的构造与解释》？

13，熟悉项目构建原理，compiler, assembler, linker， loader之类，有一本书《程序员的自我修养》有比较全面覆盖。

[编译器书籍 现代体系结构的优化编译器 高级编译器设计与实现](https://github.com/Ewenwan/compilerbook)

# 目标检测 yolov3相关  darknet框架

[YOLO_v3 TF 加强版 GN FC DA ](https://github.com/Stinky-Tofu/YOLO_V3)

[caffe 实现  MobileNet-YOLOv3 ](https://github.com/Ewenwan/MobileNet-YOLO)

[Translate darknet to tensorflow darkflow](https://github.com/thtrieu/darkflow)

[FOR Raspberry Pi 3 ](https://github.com/digitalbrain79/darknet-nnpack)

[基于YOLO的3D目标检测：YOLO-6D bounding box在2D图像上的投影的1个中心点和8个角点 + 置信度 + 类别C](https://zhuanlan.zhihu.com/p/41790888)

[yolov1 赛灵思（Xilinx） ZCU102 SoC 16bit量化 x86 / ARM  NEON优化加速](https://github.com/Ewenwan/YOLO_quantize)

* YOLO-v1 论文翻译
[You Only Look Once: Unified, Real-Time Object Detection](https://arxiv.org/abs/1506.02640)
[中文版](http://noahsnail.com/2017/08/02/2017-8-2-YOLO%E8%AE%BA%E6%96%87%E7%BF%BB%E8%AF%91%E2%80%94%E2%80%94%E4%B8%AD%E6%96%87%E7%89%88/)
[中英文对照](http://noahsnail.com/2017/08/02/2017-8-2-YOLO%E8%AE%BA%E6%96%87%E7%BF%BB%E8%AF%91%E2%80%94%E2%80%94%E4%B8%AD%E8%8B%B1%E6%96%87%E5%AF%B9%E7%85%A7/)

* YOLO-v2 YOLO9000  
[YOLO9000: Better, Faster, Stronger](https://arxiv.org/abs/1612.08242)
[中文版](http://noahsnail.com/2017/12/26/2017-12-26-YOLO9000,%20Better,%20Faster,%20Stronger%E8%AE%BA%E6%96%87%E7%BF%BB%E8%AF%91%E2%80%94%E2%80%94%E4%B8%AD%E6%96%87%E7%89%88/)
[中英文对照](http://noahsnail.com/2017/12/26/2017-12-26-YOLO9000,%20Better,%20Faster,%20Stronger%E8%AE%BA%E6%96%87%E7%BF%BB%E8%AF%91%E2%80%94%E2%80%94%E4%B8%AD%E8%8B%B1%E6%96%87%E5%AF%B9%E7%85%A7/)

[自动标注图片工具 A self automatically labeling tool ](https://github.com/eric612/AutoLabelImg)

## 0. darknet 项目主页
[darknet yolov3](https://pjreddie.com/darknet/yolo/)

[darknet yolov3 from scratch in PyTorch 详细](https://blog.paperspace.com/how-to-implement-a-yolo-object-detector-in-pytorch/)

[yolov3 PyTorch github ](https://github.com/ayooshkathuria/YOLO_v3_tutorial_from_scratch)

[darknet yolov2](https://pjreddie.com/darknet/yolov2/)

[darknet yolov1](https://pjreddie.com/darknet/yolov1/)

[YOLOv3_SpringEdition  C++ Windows and Linux interface library. (Train,Detect both) ](https://github.com/Ewenwan/YOLOv3_SpringEdition)


# yolov3改进
## 1. 多级预测(多尺度预测)
    终于为 YOLO 增加了 top down 的多级预测，解决了 YOLO 颗粒度粗，对小目标无力的问题。
    v2 只有一个 detection，v3 一下变成了 3 个，分别是一个下采样的，feature map 为 13*13，
    还有 2 个上采样的 eltwise sum，feature map 为 26*26，52*52，
    也就是说 v3 的 416 版本已经用到了 52 的 feature map，
    而 v2 把多尺度考虑到训练的 data 采样上，最后也只是用到了 13 的 feature map，这应该是对小目标影响最大的地方。
    在论文中从单层预测五种 boundingbox 变成 每层 3 种 boundongbox(3*3=9种)。
    
## 2. loss不同

    作者 v3 替换了 v2 的 softmax loss 变成 logistic loss，
    由于每个点所对应的 bounding box 少并且差异大，
    每个 bounding 与 ground truth 的 matching 策略变成了 1 对 1。
    
    当预测的目标类别很复杂的时候，采用 logistic regression 进行分类是更有效的，
    比如在 Open Images Dataset 数据集进行分类。
    在这个数据集中，会有很多重叠的标签，比如女人、人，
    如果使用 softmax 则意味着每个候选框只对应着一个类别，但是实际上并不总是这样。
    复合标签的方法能对数据进行更好的建模。
    
## 3. 加深网络
    采用简化的 residual block 取代了原来 1×1 和 3×3 的 block,
    其实就是加了一个 shortcut(直通捷径)，也是网络加深必然所要采取的手段(梯度就可以传播的更远)。
    这和上一点是有关系的，v2 的 darknet-19 变成了 v3 的 darknet-53，
    为啥呢？就是需要上采样啊，卷积层的数量自然就多了，
    另外作者还是用了一连串的  3*3、1*1 卷积，3*3 的卷积增加 channel，
    而 1*1 的卷积在于压缩 3*3 卷积后的特征表示。

## 4. Router
    由于 top down 的多级预测，进而改变了 router（或者说 concatenate，不同尺度特征的融合方式）时的方式，
    将原来诡异的 reorg(大尺度拆分成小尺度) 改成了 upsample(上采样合并)。
## 说点题外话
    YOLO 让人联想到龙珠里的沙鲁（cell），不断吸收同化对手，进化自己，提升战斗力：
    YOLOv1 吸收了 SSD 的长处（加了 BN 层，扩大输入维度，使用了 Anchor，训练的时候数据增强），进化到了 YOLOv2； 
    吸收 DSSD 和 FPN 的长处，仿 ResNet 的 Darknet-53，仿 SqueezeNet 的纵横交叉网络，又进化到 YOLO 第三形态。 
    
# 代码实现
[](https://xmfbit.github.io/2018/04/01/paper-yolov3/)

    在v3中，作者新建了一个名为yolo的layer，其参数如下：
```asm
[yolo]
mask = 0,1,2
## 9组anchor对应9个框框
anchors = 10,13,  16,30,  33,23,  30,61,  62,45,  59,119,  116,90,  156,198,  373,326
classes=20   ## VOC20类
num=9
jitter=.3
ignore_thresh = .5
truth_thresh = 1
random=1
``` 
    打开yolo_layer.c文件，找到forward部分代码。
    可以看到，首先，对输入进行activation。
    注意，如论文所说，对类别进行预测的时候，
    没有使用v2中的softmax或softmax tree，而是直接使用了logistic变换。
```c
for (b = 0; b < l.batch; ++b){
    for(n = 0; n < l.n; ++n){
        int index = entry_index(l, b, n*l.w*l.h, 0);
        // 对 tx, ty(4个边框参数) 进行logistic变换
        activate_array(l.output + index, 2*l.w*l.h, LOGISTIC);
        index = entry_index(l, b, n*l.w*l.h, 4);
        // 对confidence和C类 进行logistic变换
        activate_array(l.output + index, (1+l.classes)*l.w*l.h, LOGISTIC);
    }
}
```
## 我们看一下如何计算梯度
```c
for (j = 0; j < l.h; ++j) {
    for (i = 0; i < l.w; ++i) {
        for (n = 0; n < l.n; ++n) {
            // 对每个预测的 bounding box
            // 找到与其IoU最大的 ground truth
            int box_index = entry_index(l, b, n*l.w*l.h + j*l.w + i, 0);
            box pred = get_yolo_box(l.output, l.biases, l.mask[n], box_index, i, j, l.w, l.h, net.w, net.h, l.w*l.h);
            float best_iou = 0;
            int best_t = 0;
            for(t = 0; t < l.max_boxes; ++t){
                box truth = float_to_box(net.truth + t*(4 + 1) + b*l.truths, 1);
                if(!truth.x) break;
                float iou = box_iou(pred, truth);
                if (iou > best_iou) {
                    best_iou = iou;
                    best_t = t;
                }
            }
            int obj_index = entry_index(l, b, n*l.w*l.h + j*l.w + i, 4);
            avg_anyobj += l.output[obj_index];
            // 计算梯度
            // 如果大于ignore_thresh, 那么忽略
            // 如果小于ignore_thresh，target = 0
            // diff = -gradient = target - output
            // 为什么是上式，见下面的数学分析
            l.delta[obj_index] = 0 - l.output[obj_index];
            if (best_iou > l.ignore_thresh) {
                l.delta[obj_index] = 0;
            }
            // 这里仍然有疑问，为何使用 truth_thresh? 这个值是1
            // 按道理，iou无论如何不可能大于1啊。。。
            if (best_iou > l.truth_thresh) {
                // confidence target = 1
                l.delta[obj_index] = 1 - l.output[obj_index];
                int class = net.truth[best_t*(4 + 1) + b*l.truths + 4];
                if (l.map) class = l.map[class];
                int class_index = entry_index(l, b, n*l.w*l.h + j*l.w + i, 4 + 1);
                // 对class进行求导
                delta_yolo_class(l.output, l.delta, class_index, class, l.classes, l.w*l.h, 0);
                box truth = float_to_box(net.truth + best_t*(4 + 1) + b*l.truths, 1);
                // 对box位置参数进行求导
                delta_yolo_box(truth, l.output, l.biases, l.mask[n], box_index, i, j, l.w, l.h, net.w, net.h, l.delta, (2-truth.w*truth.h), l.w*l.h);
            }
        }
    }
}

```
## 下面，我们看下两个关键的子函数，delta_yolo_class和delta_yolo_box的实现。
```c
// class是类别的ground truth
// classes是类别总数
// index是feature map一维数组里面class prediction的起始索引
void delta_yolo_class(float *output, float *delta, int index, 
  int class, int classes, int stride, float *avg_cat) {
    int n;
    // 这里暂时不懂
    if (delta[index]){
        delta[index + stride*class] = 1 - output[index + stride*class];
        if(avg_cat) *avg_cat += output[index + stride*class];
        return;
    }
    for(n = 0; n < classes; ++n){
        // 见上，diff = target - prediction
        delta[index + stride*n] = ((n == class)?1 : 0) - output[index + stride*n];
        if(n == class && avg_cat) *avg_cat += output[index + stride*n];
    }
}
// box delta这里没什么可说的，就是square error的求导
float delta_yolo_box(box truth, float *x, float *biases, int n, 
  int index, int i, int j, int lw, int lh, int w, int h, 
  float *delta, float scale, int stride) {
    box pred = get_yolo_box(x, biases, n, index, i, j, lw, lh, w, h, stride);
    float iou = box_iou(pred, truth);
    float tx = (truth.x*lw - i);
    float ty = (truth.y*lh - j);
    float tw = log(truth.w*w / biases[2*n]);
    float th = log(truth.h*h / biases[2*n + 1]);
    delta[index + 0*stride] = scale * (tx - x[index + 0*stride]);
    delta[index + 1*stride] = scale * (ty - x[index + 1*stride]);
    delta[index + 2*stride] = scale * (tw - x[index + 2*stride]);
    delta[index + 3*stride] = scale * (th - x[index + 3*stride]);
    return iou;
}
```
# 上面，我们遍历了每一个prediction的bounding box，下面我们还要遍历每个ground truth，根据IoU，为其分配一个最佳的匹配。

```c
// 遍历ground truth
for(t = 0; t < l.max_boxes; ++t){
    box truth = float_to_box(net.truth + t*(4 + 1) + b*l.truths, 1);
    if(!truth.x) break;
    // 找到iou最大的那个bounding box
    float best_iou = 0;
    int best_n = 0;
    i = (truth.x * l.w);
    j = (truth.y * l.h);
    box truth_shift = truth;
    truth_shift.x = truth_shift.y = 0;
    for(n = 0; n < l.total; ++n){
        box pred = {0};
        pred.w = l.biases[2*n]/net.w;
        pred.h = l.biases[2*n+1]/net.h;
        float iou = box_iou(pred, truth_shift);
        if (iou > best_iou){
            best_iou = iou;
            best_n = n;
        }
    }
    
    int mask_n = int_index(l.mask, best_n, l.n);
    if(mask_n >= 0){
        int box_index = entry_index(l, b, mask_n*l.w*l.h + j*l.w + i, 0);
        float iou = delta_yolo_box(truth, l.output, l.biases, best_n, 
          box_index, i, j, l.w, l.h, net.w, net.h, l.delta, 
          (2-truth.w*truth.h), l.w*l.h);
        int obj_index = entry_index(l, b, mask_n*l.w*l.h + j*l.w + i, 4);
        avg_obj += l.output[obj_index];
        // 对应objectness target = 1
        l.delta[obj_index] = 1 - l.output[obj_index];
        int class = net.truth[t*(4 + 1) + b*l.truths + 4];
        if (l.map) class = l.map[class];
        int class_index = entry_index(l, b, mask_n*l.w*l.h + j*l.w + i, 4 + 1);
        delta_yolo_class(l.output, l.delta, class_index, class, l.classes, l.w*l.h, &avg_cat);
        ++count;
        ++class_count;
        if(iou > .5) recall += 1;
        if(iou > .75) recall75 += 1;
        avg_iou += iou;
    }
}

```

    =============================================
    =============================================
  ## 1.安装 编译darknet
    git clone https://github.com/pjreddie/darknet
    cd darknet
    make
    
[opencv](https://github.com/Ewenwan/MVision/blob/master/opencv_app/readme.md)安装

    安装了 opencv之后 可以打开opencv的编译选项
    还有多线程 openMP选项
    OPENCV=1
    OPENMP=1

    问题    problem:
    /usr/bin/ld: 找不到 -lippicv
    解决办法 solution:

    pkg-config加载库的路径是/usr/local/lib,我们去这这个路径下看看，
    发现没有-lippicv对应的库，别的选项都有对应的库，然后我们把-lippicv对应的库（libippicv.a）
    放到这个路径下就好啦了。

    我的liboppicv.a 在../opencv-3.1.0/3rdparty/ippicv/unpack/ippicv_lnx/lib/intel64/liboppicv.a
    这个路径下。

    你的也在你自己opencv文件夹的对应路径下。
    先cd 到上面这个路径下，然后sudo cp liboppicv.a /usr/local/lib 
    将这个库文件复制到/usr/local/lib下就好了。
    
    查看 opencv 是否安装成功
    pkg-config --modversion opencv 
    
    
### 如需GPU 注意千万不要忘了修改nvcc  实际cuda 安装路径
    nvcc=/usr/local/cuda-8.0/bin/nvcc
  
### 问题 找不到 libopencv_shape.so.3.0: cannot open shared object file: No such file or directory 
    进入目录：cd /etc/ld.so.conf.d
    创建：sudo vim opencv.conf
    添加：/usr/local/lib           opencv的实际安装路径
    执行：sudo ldconfig

[caffe的安装](https://blog.csdn.net/yhaolpz/article/details/71375762)

### scikit-image 安装
    命令行安装 sudo apt-get install python-skimage
    
    源码安装
    git clone https://github.com/scikit-image/scikit-image.git

    安装所有必需的依赖项:
    sudo apt-get install python-matplotlib python-numpy python-pil python-scipy python-

    使用已经安装好的的编译器:
    sudo apt-get install build-essential cython


    cd scikit-image
    如果你的编译工具完全的话，直接运行:
    pip install -U -e .
    
[cython 0.25 版本](https://packages.ubuntu.com/artful/cython)
    
    安装 sudo dpkg -i cython_0.25.2-2build3_amd64.deb 
    
    更新:
    git pull  # Grab latest source
    python setup.py build_ext -i  # Compile any modified extensions

###  from google.protobuf.internal import enum_type_wrapper ImportError: No module named google.protobuf
    sudo apt-get install python-protobuf

============================================
    =============================================
  ## 2.下载训练好的权重weight文件
      yolov3
      wget https://pjreddie.com/media/files/yolov3.weights   对于coco数据集的


      yolo v2 的权重 大 网络
      wget https://pjreddie.com/media/files/yolov2.weights         对于 coco数据集     yolov2.cfg
      ./darknet detect cfg/yolov2.cfg yolov2.weights data/dog.jpg  检测
      yolo v2 的权重 小 网络
      wget https://pjreddie.com/media/files/yolov2-tiny.weights    对于 coco数据集     yolov2-tiny.cfg
      ./darknet detect cfg/yolov2-tiny.cfg yolov2-tiny.weights data/dog.jpg  检测

       yolo v2 的权重 大 网络
      wget https://pjreddie.com/media/files/yolov2-voc.weights        对于 voc数据集   yolov2-voc.cfg
      ./darknet detect cfg/yolov2-voc.cfg yolov2.weights data/dog.jpg  检测
      yolo v2 的权重 小 网络
      wget https://pjreddie.com/media/files/yolov2-tiny-voc.weights    对于 voc数据集     yolov2-tiny-voc.cfg
      ./darknet detect cfg/yolov2-tiny-voc.cfg yolov2-tiny-voc.weights data/dog.jpg  检测


      yolo v1 的权重 大 网络
      wget http://pjreddie.com/media/files/yolov1/yolov1.weights       对于 voc数据集
      ./darknet yolo test cfg/yolov1/yolo.cfg yolov1.weights data/dog.jpg   检测

      yolo v1 的权重 小 网络
      wget http://pjreddie.com/media/files/yolov1/tiny-yolov1.weights  对于 voc数据集
      ./darknet yolo test cfg/yolov1/tiny-yolo.cfg tiny-yolov1.weights data/person.jpg 检测

    =============================================
    =============================================
  ## 3.执行检测网络  标出框已经分类 和 置信度

      a.  yolo v3 检测
          ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg
          输出信息：
          (模型结构 和 置信度 检测时间 等信息  cpu上 6-12s/张 )
      layer     filters    size              input                output
          0 conv     32  3 x 3 / 1   416 x 416 x   3   --->   416 x 416 x  32  0.299 GFLOPs  all: 0.299 GFLOPs
          1 conv     64  3 x 3 / 2   416 x 416 x  32   --->   208 x 208 x  64  1.595 GFLOPs  all: 1.894 GFLOPs
          2 conv     32  1 x 1 / 1   208 x 208 x  64   --->   208 x 208 x  32  0.177 GFLOPs  all: 2.071 GFLOPs
          3 conv     64  3 x 3 / 1   208 x 208 x  32   --->   208 x 208 x  64  1.595 GFLOPs  all: 3.666 GFLOPs
          4 res    1                 208 x 208 x  64   ->   208 x 208 x  64
          5 conv    128  3 x 3 / 2   208 x 208 x  64   --->   104 x 104 x 128  1.595 GFLOPs  all: 5.261 GFLOPs
          6 conv     64  1 x 1 / 1   104 x 104 x 128   --->   104 x 104 x  64  0.177 GFLOPs  all: 5.438 GFLOPs
          7 conv    128  3 x 3 / 1   104 x 104 x  64   --->   104 x 104 x 128  1.595 GFLOPs  all: 7.033 GFLOPs
          8 res    5                 104 x 104 x 128   ->   104 x 104 x 128
          9 conv     64  1 x 1 / 1   104 x 104 x 128   --->   104 x 104 x  64  0.177 GFLOPs  all: 7.210 GFLOPs
         10 conv    128  3 x 3 / 1   104 x 104 x  64   --->   104 x 104 x 128  1.595 GFLOPs  all: 8.805 GFLOPs
         11 res    8                 104 x 104 x 128   ->   104 x 104 x 128
         12 conv    256  3 x 3 / 2   104 x 104 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 10.400 GFLOPs
         13 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 10.577 GFLOPs
         14 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 12.172 GFLOPs
         15 res   12                  52 x  52 x 256   ->    52 x  52 x 256
         16 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 12.349 GFLOPs
         17 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 13.944 GFLOPs
         18 res   15                  52 x  52 x 256   ->    52 x  52 x 256
         19 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 14.121 GFLOPs
         20 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 15.716 GFLOPs
         21 res   18                  52 x  52 x 256   ->    52 x  52 x 256
         22 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 15.893 GFLOPs
         23 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 17.488 GFLOPs
         24 res   21                  52 x  52 x 256   ->    52 x  52 x 256
         25 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 17.666 GFLOPs
         26 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 19.260 GFLOPs
         27 res   24                  52 x  52 x 256   ->    52 x  52 x 256
         28 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 19.438 GFLOPs
         29 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 21.033 GFLOPs
         30 res   27                  52 x  52 x 256   ->    52 x  52 x 256
         31 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 21.210 GFLOPs
         32 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 22.805 GFLOPs
         33 res   30                  52 x  52 x 256   ->    52 x  52 x 256
         34 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 22.982 GFLOPs
         35 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 24.577 GFLOPs
         36 res   33                  52 x  52 x 256   ->    52 x  52 x 256
         37 conv    512  3 x 3 / 2    52 x  52 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 26.172 GFLOPs
         38 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 26.349 GFLOPs
         39 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 27.944 GFLOPs
         40 res   37                  26 x  26 x 512   ->    26 x  26 x 512
         41 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 28.121 GFLOPs
         42 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 29.716 GFLOPs
         43 res   40                  26 x  26 x 512   ->    26 x  26 x 512
         44 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 29.893 GFLOPs
         45 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 31.488 GFLOPs
         46 res   43                  26 x  26 x 512   ->    26 x  26 x 512
         47 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 31.665 GFLOPs
         48 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 33.260 GFLOPs
         49 res   46                  26 x  26 x 512   ->    26 x  26 x 512
         50 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 33.437 GFLOPs
         51 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 35.032 GFLOPs
         52 res   49                  26 x  26 x 512   ->    26 x  26 x 512
         53 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 35.209 GFLOPs
         54 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 36.804 GFLOPs
         55 res   52                  26 x  26 x 512   ->    26 x  26 x 512
         56 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 36.981 GFLOPs
         57 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 38.576 GFLOPs
         58 res   55                  26 x  26 x 512   ->    26 x  26 x 512
         59 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 38.753 GFLOPs
         60 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 40.348 GFLOPs
         61 res   58                  26 x  26 x 512   ->    26 x  26 x 512
         62 conv   1024  3 x 3 / 2    26 x  26 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 41.943 GFLOPs
         63 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 42.120 GFLOPs
         64 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 43.715 GFLOPs
         65 res   62                  13 x  13 x1024   ->    13 x  13 x1024
         66 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 43.893 GFLOPs
         67 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 45.487 GFLOPs
         68 res   65                  13 x  13 x1024   ->    13 x  13 x1024
         69 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 45.665 GFLOPs
         70 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 47.260 GFLOPs
         71 res   68                  13 x  13 x1024   ->    13 x  13 x1024
         72 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 47.437 GFLOPs
         73 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 49.032 GFLOPs
         74 res   71                  13 x  13 x1024   ->    13 x  13 x1024
         75 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 49.209 GFLOPs
         76 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 50.804 GFLOPs
         77 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 50.981 GFLOPs
         78 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 52.576 GFLOPs
         79 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 52.753 GFLOPs
         80 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 54.348 GFLOPs
         81 conv    255  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 255  0.088 GFLOPs  all: 54.436 GFLOPs
         82 detection
         83 route  79
         84 conv    256  1 x 1 / 1    13 x  13 x 512   --->    13 x  13 x 256  0.044 GFLOPs  all: 54.480 GFLOPs
         85 upsample            2x    13 x  13 x 256   ->    26 x  26 x 256
         86 route  85 61
         87 conv    256  1 x 1 / 1    26 x  26 x 768   --->    26 x  26 x 256  0.266 GFLOPs  all: 54.746 GFLOPs
         88 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 56.341 GFLOPs
         89 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 56.518 GFLOPs
         90 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 58.113 GFLOPs
         91 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 58.290 GFLOPs
         92 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 59.885 GFLOPs
         93 conv    255  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 255  0.177 GFLOPs  all: 60.062 GFLOPs
         94 detection
         95 route  91
         96 conv    128  1 x 1 / 1    26 x  26 x 256   --->    26 x  26 x 128  0.044 GFLOPs  all: 60.106 GFLOPs
         97 upsample            2x    26 x  26 x 128   ->    52 x  52 x 128
         98 route  97 36
         99 conv    128  1 x 1 / 1    52 x  52 x 384   --->    52 x  52 x 128  0.266 GFLOPs  all: 60.372 GFLOPs
        100 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 61.967 GFLOPs
        101 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 62.144 GFLOPs
        102 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 63.739 GFLOPs
        103 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 63.916 GFLOPs
        104 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 65.511 GFLOPs
        105 conv    255  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 255  0.353 GFLOPs  all: 65.864 GFLOPs
        106 detection
      Loading weights from yolov3.weights...Done!
      data/dog.jpg: Predicted in 0.025317 seconds.
      dog: 99%
      truck: 92%
      bicycle: 99%


      b. yolov2 检测
         ./darknet detect cfg/yolov2.cfg yolov2.weights data/dog.jpg
      输出信息：
         layer     filters    size              input                output
          0 conv     32  3 x 3 / 1   416 x 416 x   3   --->   416 x 416 x  32  0.299 GFLOPs  all: 0.299 GFLOPs
          1 max          2 x 2 / 2   416 x 416 x  32   ->   208 x 208 x  32
          2 conv     64  3 x 3 / 1   208 x 208 x  32   --->   208 x 208 x  64  1.595 GFLOPs  all: 1.894 GFLOPs
          3 max          2 x 2 / 2   208 x 208 x  64   ->   104 x 104 x  64
          4 conv    128  3 x 3 / 1   104 x 104 x  64   --->   104 x 104 x 128  1.595 GFLOPs  all: 3.489 GFLOPs
          5 conv     64  1 x 1 / 1   104 x 104 x 128   --->   104 x 104 x  64  0.177 GFLOPs  all: 3.666 GFLOPs
          6 conv    128  3 x 3 / 1   104 x 104 x  64   --->   104 x 104 x 128  1.595 GFLOPs  all: 5.261 GFLOPs
          7 max          2 x 2 / 2   104 x 104 x 128   ->    52 x  52 x 128
          8 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 6.856 GFLOPs
          9 conv    128  1 x 1 / 1    52 x  52 x 256   --->    52 x  52 x 128  0.177 GFLOPs  all: 7.033 GFLOPs
         10 conv    256  3 x 3 / 1    52 x  52 x 128   --->    52 x  52 x 256  1.595 GFLOPs  all: 8.628 GFLOPs
         11 max          2 x 2 / 2    52 x  52 x 256   ->    26 x  26 x 256
         12 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 10.223 GFLOPs
         13 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 10.400 GFLOPs
         14 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 11.995 GFLOPs
         15 conv    256  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x 256  0.177 GFLOPs  all: 12.172 GFLOPs
         16 conv    512  3 x 3 / 1    26 x  26 x 256   --->    26 x  26 x 512  1.595 GFLOPs  all: 13.767 GFLOPs
         17 max          2 x 2 / 2    26 x  26 x 512   ->    13 x  13 x 512
         18 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 15.362 GFLOPs
         19 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 15.539 GFLOPs
         20 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 17.134 GFLOPs
         21 conv    512  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 512  0.177 GFLOPs  all: 17.311 GFLOPs
         22 conv   1024  3 x 3 / 1    13 x  13 x 512   --->    13 x  13 x1024  1.595 GFLOPs  all: 18.906 GFLOPs
         23 conv   1024  3 x 3 / 1    13 x  13 x1024   --->    13 x  13 x1024  3.190 GFLOPs  all: 22.096 GFLOPs
         24 conv   1024  3 x 3 / 1    13 x  13 x1024   --->    13 x  13 x1024  3.190 GFLOPs  all: 25.286 GFLOPs
         25 route  16
         26 conv     64  1 x 1 / 1    26 x  26 x 512   --->    26 x  26 x  64  0.044 GFLOPs  all: 25.330 GFLOPs
         27 reorg              / 2    26 x  26 x  64   ->    13 x  13 x 256
         28 route  27 24
         29 conv   1024  3 x 3 / 1    13 x  13 x1280   --->    13 x  13 x1024  3.987 GFLOPs  all: 29.317 GFLOPs
         30 conv    425  1 x 1 / 1    13 x  13 x1024   --->    13 x  13 x 425  0.147 GFLOPs  all: 29.464 GFLOPs
         31 detection
      mask_scale: Using default '1.000000'
      Loading weights from yolov2.weights...Done!
      data/dog.jpg: Predicted in 0.009945 seconds.
      dog: 81%
      truck: 74%
      bicycle: 83%

      c. yolov1 测试
      ./darknet detector test cfg/voc_my_cfg.data cfg/yolov1.cfg ../caffe-yolo/yolov1/yolov1.weights data/dog.jpg 
      输出信息：
      layer     filters    size              input                output
          0 conv     64  7 x 7 / 2   448 x 448 x   3   --->   224 x 224 x  64  0.944 GFLOPs  all: 0.944 GFLOPs
          1 max          2 x 2 / 2   224 x 224 x  64   ->   112 x 112 x  64
          2 conv    192  3 x 3 / 1   112 x 112 x  64   --->   112 x 112 x 192  2.775 GFLOPs  all: 3.719 GFLOPs
          3 max          2 x 2 / 2   112 x 112 x 192   ->    56 x  56 x 192
          4 conv    128  1 x 1 / 1    56 x  56 x 192   --->    56 x  56 x 128  0.154 GFLOPs  all: 3.873 GFLOPs
          5 conv    256  3 x 3 / 1    56 x  56 x 128   --->    56 x  56 x 256  1.850 GFLOPs  all: 5.722 GFLOPs
          6 conv    256  1 x 1 / 1    56 x  56 x 256   --->    56 x  56 x 256  0.411 GFLOPs  all: 6.134 GFLOPs
          7 conv    512  3 x 3 / 1    56 x  56 x 256   --->    56 x  56 x 512  7.399 GFLOPs  all: 13.532 GFLOPs
          8 max          2 x 2 / 2    56 x  56 x 512   ->    28 x  28 x 512
          9 conv    256  1 x 1 / 1    28 x  28 x 512   --->    28 x  28 x 256  0.206 GFLOPs  all: 13.738 GFLOPs
         10 conv    512  3 x 3 / 1    28 x  28 x 256   --->    28 x  28 x 512  1.850 GFLOPs  all: 15.587 GFLOPs
         11 conv    256  1 x 1 / 1    28 x  28 x 512   --->    28 x  28 x 256  0.206 GFLOPs  all: 15.793 GFLOPs
         12 conv    512  3 x 3 / 1    28 x  28 x 256   --->    28 x  28 x 512  1.850 GFLOPs  all: 17.643 GFLOPs
         13 conv    256  1 x 1 / 1    28 x  28 x 512   --->    28 x  28 x 256  0.206 GFLOPs  all: 17.848 GFLOPs
         14 conv    512  3 x 3 / 1    28 x  28 x 256   --->    28 x  28 x 512  1.850 GFLOPs  all: 19.698 GFLOPs
         15 conv    256  1 x 1 / 1    28 x  28 x 512   --->    28 x  28 x 256  0.206 GFLOPs  all: 19.903 GFLOPs
         16 conv    512  3 x 3 / 1    28 x  28 x 256   --->    28 x  28 x 512  1.850 GFLOPs  all: 21.753 GFLOPs
         17 conv    512  1 x 1 / 1    28 x  28 x 512   --->    28 x  28 x 512  0.411 GFLOPs  all: 22.164 GFLOPs
         18 conv   1024  3 x 3 / 1    28 x  28 x 512   --->    28 x  28 x1024  7.399 GFLOPs  all: 29.563 GFLOPs
         19 max          2 x 2 / 2    28 x  28 x1024   ->    14 x  14 x1024
         20 conv    512  1 x 1 / 1    14 x  14 x1024   --->    14 x  14 x 512  0.206 GFLOPs  all: 29.768 GFLOPs
         21 conv   1024  3 x 3 / 1    14 x  14 x 512   --->    14 x  14 x1024  1.850 GFLOPs  all: 31.618 GFLOPs
         22 conv    512  1 x 1 / 1    14 x  14 x1024   --->    14 x  14 x 512  0.206 GFLOPs  all: 31.824 GFLOPs
         23 conv   1024  3 x 3 / 1    14 x  14 x 512   --->    14 x  14 x1024  1.850 GFLOPs  all: 33.673 GFLOPs
         24 conv   1024  3 x 3 / 1    14 x  14 x1024   --->    14 x  14 x1024  3.699 GFLOPs  all: 37.373 GFLOPs
         25 conv   1024  3 x 3 / 2    14 x  14 x1024   --->     7 x   7 x1024  0.925 GFLOPs  all: 38.298 GFLOPs
         26 conv   1024  3 x 3 / 1     7 x   7 x1024   --->     7 x   7 x1024  0.925 GFLOPs  all: 39.222 GFLOPs
         27 conv   1024  3 x 3 / 1     7 x   7 x1024   --->     7 x   7 x1024  0.925 GFLOPs  all: 40.147 GFLOPs
         28 Local Layer: 7 x 7 x 1024 image, 256 filters -> 7 x 7 x 256 image
         29 dropout       p = 0.50               12544  ->  12544
         30 connected                            12544  ->  1715
         31 Detection Layer
      forced: Using default '0'
      Loading weights from ../caffe-yolo/yolov1/yolov1.weights...Done!
      data/dog.jpg: Predicted in 1.231002 seconds.
      car: 55%

    ==============================================
    ==============================================
  ## 4. 其他图片
    data/eagle.jpg, data/dog.jpg, data/person.jpg, data/horses.jpg


    ==============================================
    ==============================================
  ## 5、较长的命令行
    ./darknet detector test cfg/coco.data cfg/yolov3.cfg yolov3.weights data/dog.jpg

    ==============================================
    ==============================================
  ## 6、检测多幅图像  会提示输入图像 检测完成 再次提示输入图像
    ./darknet detect cfg/yolov3.cfg yolov3.weights


    ==============================================
    ==============================================
  ## 7、改变检测阈值
    ./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jpg -thresh 0

    ==============================================
    ==============================================
  ## 8、网络摄像头 实时检测
    ./darknet detector demo cfg/coco.data cfg/yolov3.cfg yolov3.weights

    ==============================================
    ==============================================
## 9、时时检测视频
    ./darknet detector demo cfg/coco.data cfg/yolov3.cfg yolov3.weights <video file>


    ==============================================
    ==============================================
## 9.5 训练问题记录
[参考](https://blog.csdn.net/lilai619/article/details/79695109)
### Tips0: 数据集问题
    如果是学习如何训练，建议不要用VOC或者COCO,这两个数据集复杂，类别较多，
    复现作者的效果需要一定的功力，迭代差不多5w次，就可以看到初步的效果。
    所以，不如挑个简单数据集的或者手动标注个几百张就可以进行训练学习。
### Tips1: CUDA: out of memory 以及 resizing 问题
    显存不够，调小batch，关闭多尺度训练：random = 0。
### Tips2: 在迭代前期，loss很大，正常吗？
    经过几个数据集的测试，前期loss偏大是正常的，后面就很快收敛了。
### Tips3: YOLOV3中的mask作用？
    三个尺度上预测不同大小的框
    82卷积层 为最大的预测尺度，使用较大的mask，但是可以预测出较小的物体
    94卷积层 为中间的预测尺度，使用中等的mask，
    106卷积层为最小的预测尺度，使用较小的mask，可以预测出较大的物体
#### Tips4: YOLOV3中的num作用？ 
    总共提供9种不同尺度的先验框，
    每个尺度预测三种，先验框。预测20类的话，3*（5+20）=75
### Tips5: YOLOV3训练出现nan的问题？
    在显存允许的情况下，可适当增加batch大小，可以一定程度上减少NAN的出现
### Tips6: Anchor box作用是？
    F-rcnn使用人工指定的预设款尺寸，可能没有宏观特性
    在数据集上 对真实边框 使用 K-means 聚类得到的边款长宽比例更具有宏观特性
    预测的坐标值是，相对应格子的坐上点的偏移量
    而长宽是相对于 整幅图像大小的比例，
    b.w = exp(x[index + 2*stride]) * biases[2*n]/w
    b.h = exp(x[index + 3*stride]) * biases[2*n+1]/h
    x[] 为网络输出
    biases[]为 预设边框的大小
    意识就是说，每个格子预测的边框输出为0~1之间
    且网络输出 x[] 是相对于预设格子尺寸的 指数对数
    就是在预设格子尺寸上调整，预测输出
    
    v2 版本的格子尺寸 cfg文件中定义的是 相对于最后特征图（原图/32）
    v3 版本的格子尺寸 cfg文件中定义的是 相对于网络输入图的尺寸
### Tips7:模型什么时候保存？如何更改
    迭代次数小于1000时，每100次保存一次，大于1000时，没10000次保存一次。
    自己可以根据需求进行更改，然后重新编译即可[ 先 make clean ,然后再 make]。   
    代码位置： examples/detector.c line 138
    if(i%10000 == 0) || (i<1000 && i%100 == 0)
    
### Tips8: 中文标签
    A：首先生成对应的中文标签，
    make_labels.py 修改代码中的字体，将其替换成指中文字体，如果提示提示缺少**模块，安装就行了。
    B：添加自己的读取标签和画框函数
    
[生成对应的中文标签](/tool/make_labels_cn.py)

[修改的图像中午标签显示](/darkNet_src/image.c)

[参考我的博客](https://blog.csdn.net/xiaoxiaowenqiang/article/details/80289577)

### Tips9: 图片上添加置信值
    如果编译时没有制定opencv，基本上很难实现。如果编译时指定了opencv,在画框的函数里面添加一下就行了。
### Tips10:图片保存名称
    测试的时候，保存的默认名称是predictions.自己改成对应的图片名称即可。

## 10.在 Pascal VOC 数据集上训练
    ====================================
  ### 10.1 Pascal VOC数据集介绍：
    给定自然图片， 从中识别出特定物体。
    待识别的物体有20类：
    囊括了车、人、猫、狗等20类常见目标。训练样本较少、场景变化多端，非常具有挑战性。
      aeroplane  
      bicycle
      bird
      boat
      bottle
      bus
      car
      cat
      chair
      cow
      diningtable
      dog
      horse
      motorbike
      person
      pottedplant
      sheep
      sofa
      train
      tvmonitor

    ===================================
    
[在自己的数据集上训练](https://www.yuthon.com/2016/11/26/Train-Caffe-YOLO-on-our-own-dataset/)、

      其目录结构如下:
          .
      ├── VOC2007
      │   ├── Annotations           // 放的是.xml文件
      │   ├── ImageSets             // 稍微复杂
      │   ├── JPEGImages            // 存放的是对应的.jpg图像
      │   ├── SegmentationClass     // 语义分割类
      │   └── SegmentationObject    // 语义分割区域
      └── VOC2012
          ├── Annotations
          ├── ImageSets
          ├── JPEGImages
          ├── SegmentationClass
          └── SegmentationObject

      ImageSets目录中结构如下, 主要关注的是Main文件夹中的trainval.txt, train.txt , val.txt以及test.txt四个文件.

      .
      ├── Layout
      │   ├── test.txt
      │   ├── train.txt
      │   ├── trainval.txt
      │   └── val.txt
      ├── Main
      │   ├── aeroplane_test.txt
      │   ├── aeroplane_train.txt
      │   ├── aeroplane_trainval.txt
      │   ├── aeroplane_val.txt
      │   ├── ...
      │   ├── test.txt       //重要
      │   ├── train.txt      //重要    
      │   ├── trainval.txt   //重要
      │   └── val.txt        //重要
      └── Segmentation
          ├── test.txt
          ├── train.txt
          ├── trainval.txt
          └── val.txt


      调整自己数据集的格式 成 voc数据及格式：

      1 . 首先是把之前杂乱的图片文件名重新整理, 如下所示:

      .
      ├── image00001.jpg
      ├── image00002.jpg
      ├── image00012.jpg
      ├── ...
      ├── image04524.jpg
      ├── image04525.jpg
      └── image04526.jpg
      2. 随后用labelImg重新标注这些图. 标注完成后, 建立我们自己的数据集的结构, 
        并且将图片和标注放到对应的文件夹里:
        .
        ├── ROB2017
        │   ├── Annotations
        │   ├── ImageSets
        │   ├── JPEGImages
        │   └── JPEGImages_original
        └── scripts
            ├── clean.py
            ├── conf.json
            ├── convert_png2jpg.py
            └── split_dataset.py  

      之后写了几个脚本, 其中clean.py用来清理未标注的图片; 
      split_dataset.py用来分割训练集验证集测试集, 并且保存到ImageSets/Main中.



  ### 10.2 下载数据集：
    wget https://pjreddie.com/media/files/VOCtrainval_11-May-2012.tar
    wget https://pjreddie.com/media/files/VOCtrainval_06-Nov-2007.tar
    wget https://pjreddie.com/media/files/VOCtest_06-Nov-2007.tar
    tar xf VOCtrainval_11-May-2012.tar
    tar xf VOCtrainval_06-Nov-2007.tar
    tar xf VOCtest_06-Nov-2007.tar
    存在于 VOCdevkit/ 子目录下


    ===================================
  ### 10.3创建标记文件 .txt ：
    每个框 类别 一行  x, y, width, and height  与图像长和宽相关
    <object-class> <x> <y> <width> <height>

    运行标记文件 脚本
    run scripts/voc_label.py
    python voc_label.py

    会在  VOCdevkit/VOC2007/labels/ and VOCdevkit/VOC2012/labels/
    下生成一些列文件
    ls
    2007_test.txt   VOCdevkit
    2007_train.txt  voc_label.py
    2007_val.txt    VOCtest_06-Nov-2007.tar
    2012_train.txt  VOCtrainval_06-Nov-2007.tar
    2012_val.txt    VOCtrainval_11-May-2012.tar

    除去2007_test.txt 生成一个文件
    cat 2007_train.txt 2007_val.txt 2012_*.txt > train.txt

    ==================================
  ### 10.4 修改 数据配置文件 cfg/voc.data
      classes= 20
      train  = <path-to-voc>/train.txt
      valid  = <path-to-voc>2007_test.txt
      names = data/voc.names
      backup = backup
## 我的
    classes= 20
    train  = /home/sujun/ewenwan/software/darknet/data/voc/my_train_data.txt
    valid  = /home/sujun/ewenwan/software/darknet/data/voc/2007_test.txt
    names = data/voc.names
    backup = backup
    
### 以及 网络配置文件 
    [net]
    # Testing    # 测试模式
    # batch=1 # bigger gpu memory cost higher 
    #  subdivisions=1

    # Training   训练
    batch=64          # 一次训练使用多张图片
    subdivisions=16   # 分成16次载入gpu内存 也就是一次载入 4张图片
    width=416         # 网络输入的 宽 高 通道数量
    height=416
    channels=3
    momentum=0.9      # 动量 
    decay=0.0005      # 衰减权重
    angle=0           # 图片旋转
    saturation = 1.5  # 饱和度 图像预处理
    exposure = 1.5    # 曝光度
    hue=.1            # 色调

    learning_rate=0.0001#  bigger easy spread学习率
    burn_in=1000        # 学习率控制参数
    max_batches = 50200 # 最大迭代次数
    policy=steps        # 学习策略 随时间递减，还是按步长递减
    steps=40000,45000   # 学习率变动步长 逐步降低 学习率 牛顿下山法
    scales=.1,.1        # 学习率变动因子
    ...
    ...
    [convolutional]
    size=1
    stride=1
    pad=1
    filters=75          # 最后输出 = 3*(20+5)  三个尺度，每个尺度预测3种格子，每个格子预测20类，5个框参数
    activation=linear

    [yolo]
    mask = 0,1,2        # 前三个 预设边框尺寸  kmeans聚类的结果
    anchors = 10,13,  16,30,  33,23,  30,61,  62,45,  59,119,  116,90,  156,198,  373,326
    classes=20          # 类别数量
    num=9               # 总共的预设边框数量
    jitter=.3           # 数据扩充的抖动
    ignore_thresh = .5  # 阈值
    truth_thresh = 1   
    random=1            # 多尺度训练开关


    
    =========================================================
 ### 10.5 下载预训练分类网络参数 imagenet数据集的 分类网络参数
    yolo v3 的预训练文件
    from  darknet53 
    wget https://pjreddie.com/media/files/darknet53.conv.74   对于 yolov3.cfg / 对于 yolov3-voc.cfg 等

    yolo v2 的预训练文件
    wget https://pjreddie.com/media/files/darknet19_448.conv.23

    yolo v1 的预训练文件
    https://pjreddie.com/media/files/extraction.conv.weights   对于 yolov1.cfg
    https://pjreddie.com/media/files/darknet.conv.weights      对于 yolov1-tiny.cfg



    =========================================================
  ### 10.6 . 在  VOC 训练
    从零开始
    ./darknet detector train cfg/voc.data cfg/yolov3-voc.cfg darknet53.conv.74
    断点继续训练
    ./darknet detector train cfg/voc_my_cfg.data cfg/yolov3-voc.cfg backup/yolov3-voc.backup
    
  ### 10.7 使用训练结果 测试、
    ./darknet detect cfg/yolov3-voc.cfg backup/yolov3-voc_20000.weights data/dog.jpg
    ==========================================================
    =========================================================
    
  ### 剩下的就是等待了。
    需要注意的是，如果学习率设置的比较大，训练结果很容易发散，训练过程输出的log会有nan字样，需要减小学习率后再进行训练。
    
  ### 先 单GPU 训练
    ./darknet detector train cfg/voc.data cfg/yolov3-voc.cfg darknet53.conv.74 2>1 | tee paul_train_log.txt
  ### 多GPU训练技巧
    darknet支持多GPU，使用多GPU训练可以极大加速训练速度。
    ### 单GPU与多GPU的切换技巧
    在darknet上使用多GPU训练需要一定技巧，盲目使用多GPU训练会悲剧的发现损失一直在下降、
    recall在上升，然而Obj几乎为零,最终得到的权重文件无法预测出bounding box。

    使用多GPU训练前需要先用单GPU训练至Obj有稳定上升的趋势后（我一般在obj大于0.1后切换）
    再使用backup中备份的weights通过多GPU继续训练。
    一般情况下使用单GPU训练1000个迭代即可切换到多GPU。

    ./darknet detector train cfg/voc_my_cfg.data cfg/yolov3-voc.cfg backup/yolov3-voc_1000.weights -gpus 0,1,2,3 2>1 | sudo tee paul_train_log.txt

    nvidia-smi 差看GPU使用情况
    
  ### 使用多GPU时的学习率
    使用多GPU训练时，学习率是使用单GPU训练的n倍，n是使用GPU的个数
    
  ### 可视化训练过程的中间参数
    v3 各项参数
    A.filters数目是怎么计算的：3x(classes数目+5)，和聚类数目分布有关，论文中有说明；
    B.如果想修改默认anchors数值，使用k-means即可；
    C.如果显存很小，将random设置为0，关闭多尺度训练；
    D.其他参数如何调整，有空再补;
    E.前100次迭代loss较大，后面会很快收敛；
    log 参数：
    Region xx: cfg文件中yolo-layer的索引；
    Avg IOU:当前迭代中，预测的box与标注的box的平均交并比，越大越好，期望数值为1；
    Class:  标注物体的分类准确率，越大越好，期望数值为1；
    obj:    越大越好，期望数值为1；
    No obj: 越小越好；
    .5R:    查全率较低 以IOU=0.5为阈值时候的recall; recall = 检出的正样本/实际的正样本
    0.75R:  查全率较低 以IOU=0.75为阈值时候的recall;
    count:  正样本数目。

    训练log中各参数的意义 v2
    Region Avg IOU：平均的IOU，代表预测的bounding box和ground truth的交集与并集之比，期望该值趋近于1。
    Class:是标注物体的概率，期望该值趋近于1.
    Obj：期望该值趋近于1.
    No Obj:期望该值越来越小但不为零.
    Avg Recall：期望该值趋近1
    avg：平均损失，期望该值趋近于0

    使用train_loss_visualization.py脚本可以绘制loss变化曲线。

    保存log时会生成两个文件，文件1里保存的是网络加载信息和checkout点保存信息，paul_train_log.txt中保存的是训练信息。

    1、删除log开头的三行：
    0,1,2,3,4,5,6,7
    yolo-paul
    Learning Rate: 1e-05, Momentum: 0.9, Decay: 0.0005

    2、删除log的结尾几行，使最后一行为batch的输出，如：
    shift +g 到最后
    497001: 0.863348, 0.863348 avg, 0.001200 rate, 5.422251 seconds, 107352216 images

    3、执行extract_log.py脚本，格式化log。

    最终log格式：
    Loaded: 5.588888 seconds
    Region Avg IOU: 0.649881, Class: 0.854394, Obj: 0.476559, No Obj: 0.007302, Avg Recall: 0.737705,  count: 61
    Region Avg IOU: 0.671544, Class: 0.959081, Obj: 0.523326, No Obj: 0.006902, Avg Recall: 0.780000,  count: 50
    Region Avg IOU: 0.525841, Class: 0.815314, Obj: 0.449031, No Obj: 0.006602, Avg Recall: 0.484375,  count: 64
    Region Avg IOU: 0.583596, Class: 0.830763, Obj: 0.377681, No Obj: 0.007916, Avg Recall: 0.629214,  count: 89
    Region Avg IOU: 0.651377, Class: 0.908635, Obj: 0.460094, No Obj: 0.008060, Avg Recall: 0.753425,  count: 73
    Region Avg IOU: 0.571363, Class: 0.880554, Obj: 0.341659, No Obj: 0.007820, Avg Recall: 0.633663,  count: 101
    Region Avg IOU: 0.585424, Class: 0.935552, Obj: 0.358635, No Obj: 0.008192, Avg Recall: 0.644860,  count: 107
    Region Avg IOU: 0.599972, Class: 0.832793, Obj: 0.382910, No Obj: 0.009005, Avg Recall: 0.650602,  count: 83
    497001: 0.863348, 0.863348 avg, 0.000012 rate, 5.422251 seconds, 107352216 images


    4、修改train_loss_visualization.py中lines为log行数，并根据需要修改要跳过的行数。
    skiprows=[x for x in range(lines) if ((x%10!=9) |(x<1000))]

    运行train_loss_visualization.py会在脚本所在路径生成avg_loss.png

    从损失变化曲线可以看出，模型在100000万次迭代后损失下降速度非常慢，几乎没有下降。
    结合log和cfg文件发现，我自定义的学习率变化策略在十万次迭代时会减小十倍，
    十万次迭代后学习率下降到非常小的程度，导致损失下降速度降低。
    修改cfg中的学习率变化策略，10万次迭代时不改变学习率，30万次时再降低。

    我使用迭代97000次时的备份的checkout点来继续训练。
    ./darknet detector train cfg/voc_my_cfg.data cfg/yolov3-voc.cfg backup/yolov3-voc_97000.weights -gpus 0,1,2,3 2>1 | sudo tee paul_train_log.txt

    除了可视化loss，还可以可视化Avg IOU，Avg Recall等参数。
    可视化’Region Avg IOU’, ‘Class’, ‘Obj’, ‘No Obj’, ‘Avg Recall’,’count’
    这些参数可以使用脚本train_iou_visualization.py，使用方式和train_loss_visualization.py相同。


### 使用验证集评估模型
    评估模型可以使用命令valid（只有预测结果，没有评价预测是否正确）或recall，这两个命令都无法满足我的需求，我实现了category命令做性能评估。
    我使用迭代97000次时的备份的checkout点来继续训练。
    
    在voc_my_cfg.data 末尾添加
    eval = imagenet #有voc、coco、imagenet三种模式
    修改Detector.c文件validate_detector函数，修改阈值（默认.005）
    float thresh = .1;
    重新编译然后执行命令
    ./darknet detector valid cfg/voc_my_cfg.data cfg/yolov3-voc.cfg backup/yolov3-voc_final.weights


### 想要查看recall可以使用recall命令。

    修改 Detector.c文件的validate_detector_recall函数：

    1、修改阈值：
    float thresh = .25;

    2、修改验证集路径：
    list *plist = get_paths("/mnt/large4t/pengchong_data/Data/Paul/filelist/val.txt");

    3、增加Precision
    //fprintf(stderr, "%5d %5d %5d\tRPs/Img: %.2f\tIOU: %.2f%%\tRecall:%.2f%%\n", i, correct, total, (float)proposals/(i+1), avg_iou*100/total, 100.*correct/total);
    fprintf(stderr, "ID:%5d Correct:%5d Total:%5d\tRPs/Img: %.2f\tIOU: %.2f%%\tRecall:%.2f%%\t", i, correct, total, (float)proposals/(i+1), avg_iou*100/total, 100.*correct/total);
    fprintf(stderr, "proposals:%5d\tPrecision:%.2f%%\n",proposals,100.*correct/(float)proposals
    4、执行命令
    ./darknet detector recall cfg/voc_my_cfg.data cfg/yolov3-voc.cfg backup/yolov3-voc_final.weights
[训练参考](https://blog.csdn.net/hrsstudy/article/details/65644517?utm_source=itdadao&utm_medium=referral)

## 11 在coco数据集上训练
[数据集主页](http://cocodataset.org/)

    微软发布的COCO数据库, 除了图片以外还提供物体检测, 分割(segmentation)和对图像的语义文本描述信息.
    
[COCO数据库的网址是: MS COCO API - ](http://mscoco.org/) 

[Github网址 -  ](https://github.com/pdollar/coco)

[关于API更多的细节在网站: ](http://mscoco.org/dataset/#download) 

    数据库提供Matlab, Python和Lua的API接口. 其中matlab和python的API接口可以提供完整的图像标签数据的加载, 
    parsing和可视化.此外,网站还提供了数据相关的文章, 教程等. 在使用COCO数据库提供的API和demo时, 需要首先下载COCO的图像和标签数据.

### 11.1 COCO的数据标注信息包括: 
      - 类别标志 
      - 类别数量区分 
      - 像素级的分割 
      COCO数据集有超过 200,000 张图片，80种物体类别. 所有的物体实例都用详细的分割mask进行了标注，共标注了超过 500,000 个物体实体.     
      {    
      person  # 1    
      vehicle 交通工具 #8        
      { bicycle         自行车
      car             小汽车       
      motorcycle      摩托车
      airplane        飞机       
      bus             公交车
      train           火车       
      truck           卡车
      boat}           船    
      outdoor  室外#5        
      { traffic light   交通灯     
      fire hydrant    消防栓     
      stop sign       
      parking meter      
      bench}    
      animal  动物 #10        
      { bird       
      cat      
      dog      
      horse       
      sheep      
      cow       
      elephant      
      bear       
      zebra      
      giraffe}   
      accessory 饰品 #5        
      { backpack 背包       
      umbrella 雨伞       
      handbag 手提包       
      tie 领带       
      suitcase 手提箱 }   
      sports  运动 #10        
      { frisbee      
      skis      
      snowboard       
      sports ball       
      kite        
      baseball bat       
      baseball glove       
      skateboard        
      surfboard       
      tennis racket        } 

      kitchen  厨房 #7       
      { bottle        
      wine glass       
      cup       
      fork        
      knife       
      spoon        
      bowl        }  
      food  食物#10        
      { banana        
      apple       
      sandwich        
      orange       
      broccoli       
      carrot        
      hot dog        
      pizza       
      donut       
      cake        }    
      furniture 家具 #6        
      { chair       
      couch       
      potted plant       
      bed        
      dining table       
      toilet        }    
      electronic 电子产品 #6        
      { tv        
      laptop       
      mouse        
      remote        
      keyboard        
      cell phone        }   
      appliance 家用电器 #5        
      { microwave       
      oven        
      toaster       
      sink        
      refrigerator        }    
      indoor  室内物品#7        
      { book        
      clock       
      vase     
      scissors        
      teddy bear        
      hair drier       
      toothbrush        }}
      
## 11.2下载数据集   
    cp scripts/get_coco_dataset.sh data
    cd data
    bash get_coco_dataset.sh

    脚本细节
    1. 下载 数据库API
     git clone https://github.com/pdollar/coco
     cd coco
    2. 创建 images文件夹 并下载 图像数据 解压
     在images文件夹下下载  点击链接可直接下载
     wget -c https://pjreddie.com/media/files/train2014.zip
     wget -c https://pjreddie.com/media/files/val2014.zip

     解压
     unzip -q train2014.zip
     unzip -q val2014.zip
    3. 下载标注文件等
      cd ..
      wget -c https://pjreddie.com/media/files/instances_train-val2014.zip
      wget -c https://pjreddie.com/media/files/coco/5k.part
      wget -c https://pjreddie.com/media/files/coco/trainvalno5k.part
      wget -c https://pjreddie.com/media/files/coco/labels.tgz
      sudo tar xzf labels.tgz                        标签
      sudo unzip -q instances_train-val2014.zip     分割  得到 annotations  实例分割

      生成训练/测试图像列表文件
      paste <(awk "{print \"$PWD\"}" <5k.part) 5k.part | tr -d '\t' > 5k.txt   测试验证数据
      paste <(awk "{print \"$PWD\"}" <trainvalno5k.part) trainvalno5k.part | tr -d '\t' > trainvalno5k.txt  训练数据

## 11.3修改 coco数据集的配置文件
    vim cfg/coco_my.data
    
    classes= 80
    train  = <path-to-coco>/trainvalno5k.txt
    valid  = <path-to-coco>/5k.txt
    names = data/coco.names
    backup = backup
    
    
    
## 修改模型配置文件 
    cp cfg/yolov3.cfg yolov3_my.cfg
    vim yolov3_my.cfg
## 训练
    ./darknet detector train cfg/coco_my.data cfg/yolov3_my.cfg darknet53.conv.74 2>1 -gpus 1 2>1 | sudo tee coco_train_log.txt
### 多gpu训练 记录log 以便可视化loss
    ./darknet detector train cfg/coco.data cfg/yolov3.cfg darknet53.conv.74 -gpus 0,1,2,3 2>1 | sudo tee paul_train_log.txt
### 中断后 断点接着 训练
    ./darknet detector train cfg/coco.data cfg/yolov3.cfg backup/yolov3.backup -gpus 0,1,2,3


