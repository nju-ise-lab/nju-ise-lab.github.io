---
title: "iSE 团队在源代码搜索方面取得重要进展"
date: "2023-12-05T20:02:02+08:00"
event_time: "2023-12-05T20:02:02+08:00"
category: "讲座"
creator: "iSE实验室"
location: "iSE实验室"
legacy_id: 28
views_seed: 293
draft: true
archived: true
url: "/activities/ise/"
---

<p style="text-indent: 2em; text-align: left;">源代码搜索研究旨在基于软件开发者的自然语言查询从大规模代码库中检索语义匹配的源代码，从而提升软件开发效率。该研究的主要技术挑战在于代码语义的捕捉与表示。现有方法大多是基于代码文本（Token序列）或结构（AST、CFG等）获取代码语义，然后引入了众多先进的深度学习模型来表示代码语义。然后现有方法因在代码特征捕捉时丢失了其他方面语义信息（例如数据依赖、控制依赖等）使得代码搜索性能表现不佳。</p><p style="text-indent: 2em; text-align: left;"><br></p><p style="text-indent: 24pt; text-align: left;">我院 iSE 团队房春荣老师指导博士生孙伟松创新性地提出了一种基于上下文意识代码翻译技术的源代码搜索方法 TranCS。该方法首先将编程语言编写的代码转变成语义保留的自然语言描述——翻译。翻译保留了代码的完整上下文，包括代码语句之间的常量和变量依赖、控制依赖和数据依赖。同时，翻译与自然语言查询同质。其次，该方法使用共享的单词映射机制为翻译和查询生成语义一致的嵌入表示。最后，该方法使用基于深度学习的的序列嵌入技术将翻译和查询映射到统一向量空间，然后进行翻译与查询的语义匹配，完成代码搜索任务。在大规模数据集上的实验结果表明，该技术可以显著提高代码搜索的准确性。</p><p style="text-indent: 24pt; text-align: left;"><br></p><p style="text-align: center;"><img src="https://software.nju.edu.cn/DFS//file/2021/12/20/20211220141825193r5sg9t.png" alt="" data-href="" style="width: 800px;"></p><p style="text-align: start;"><br></p><p style="text-indent: 24pt; text-align: left;">以我院博士生孙伟松为第一作者的相关研究成果《Code Search based on Context-aware Code Translation》已被软件工程领域国际顶级会议International Conference on Software Engineering（ICSE 2022，CCF A类）录用。该成果正在完善工具链进行企业合作转化。孙伟松同学前期关于测试代码抄袭检测的研究"MAF: Method-anchored test fragmentation for test code plagiarism detection"被ICSE 2019教育类录用，支撑了IEEE国际软件测试大赛和全国大学生软件测试大赛的顺利举行。</p>
