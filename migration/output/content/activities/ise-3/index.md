---
title: " iSE 实验室在移动应用测试方面取得新进展"
date: "2023-12-01T16:00:00+08:00"
event_time: "2023-12-01T16:00:00+08:00"
category: "讲座"
creator: " iSE实验室"
location: "iSE实验室"
legacy_id: 26
views_seed: 95
draft: false
url: "/activities/ise-3/"
---

<p style="text-indent: 2em; text-align: left;">自动化测试是提升移动应用质量保障的有效手段之一。现有的自动化测试技术往往只关注单设备的测试结果，而忽略了不同设备之间测试结果的内部关联。由于Oracle难以自动化判定的问题，当前的报告生成方法只能对测试结果进行简单整理，形成具有一定可读性的测试报告。然而，移动平台具有开发模式开放、运行环境多样、设备交互频繁、物理场景复杂等泛在操作系统特性，导致自动化测试在大规模移动设备集群中进行测试时，产生重复数量多、不确定性强、缺陷根因不清晰的测试报告，进而给开发人员对于移动应用测试报告的审查带来极大负担。</p><p style="text-align: start;"><br></p><p style="text-align: center;"><img src="https://software.nju.edu.cn/DFS//wordimp/rpv//xyxw/i247967/image1.png" alt="" data-href="" style="width: 740px;height: 379px;"></p><p style="text-align: start;"><br></p><p style="text-indent: 2em; text-align: left;">为解决上述问题，iSE实验室房春荣老师指导博士生虞圣呈，与华东师范大学苏亭教授深入合作，创新地提出了基于大规模多源异构数据分析的测试报告生成方法。该方法深入研究了同一待测应用在不同硬件设备和软件运行环境的情况下所产生测试结果的相互关联及内在差异，首次提出了测试不一致性标签，并进一步结合测试过程中所收集的设备数据、屏幕截图、测试事件等异构数据，构建了一个统一的多源异构数据结构化缺陷模型。基于从海量设备集群测试结果中提取的异构数据，该结构化缺陷模型根据366,357个缺陷结果生成结构化缺陷实例，从而构建了包含测试结果不一致性分析异构缺陷分类法，结合不一致性标签所反映出来的缺陷根因，进行多设备测试结果分类去重。进而通过不一致性标签、结构化缺陷模型、异构缺陷分类法三位一体相互协作，该工作实现了高质量的测试报告生成。实验结果证明该方法能够有效进行缺陷的分类与去重，并进一步生成具有高可理解性和高可读性的测试报告。同时，该工作通过一项用户调研证明了所生成的测试报告可以提高开发者缺陷检查和修复的效率。</p><p style="text-align: start;"><br></p><p style="text-indent: 2em; text-align: left;">该工作探索了泛在计算环境中的测试报告生成问题，首次通过挖掘泛在计算环境下大规模、多源、异构的设备集群中测试结果，提出了该环境下多源异构信息语义的的内在关联与差异，实现了高质量高可读测试报告的生成，对泛在操作系统开源生态质量保障具有重要意义。该工作相关成果《Test Report Generation for Android App Testing via Heterogeneous Data Analysis》已被IEEE Transactions on Software Engineering（CCF-A期刊）录用。</p><p style="text-indent: 2em; text-align: left;"><br></p><p style="text-indent: 2em; text-align: left;">虞圣呈同学由陈振宇教授和房春荣助理研究员共同指导，其主要研究方向包括自动化GUI测试和众包测试，已在TSE，ICSE等软件工程顶级学术期刊和会议发表论文4篇。此外，虞圣呈同学在ICSE、ESEC/FSE、ISSTA、ASE等顶级会议中发表5篇工具原型论文，相关成果已在国家电网、广东软件园、通行宝、龙测等企业得到初步应用。</p>
