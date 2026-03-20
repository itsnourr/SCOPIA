package com.forensic.service;

import com.forensic.entity.Node;
// import com.forensic.entity.Link;
import com.forensic.dto.GraphDto;
import com.forensic.entity.Link;
import com.forensic.repository.NodeRepository;
import com.forensic.repository.LinkRepository;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.Map;
import java.util.List;

// import org.springframework.data.domain.Page;
// import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
// import org.springframework.transaction.annotation.Transactional;

// import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class GraphService {

    private final NodeRepository nodeRepo;
    private final LinkRepository linkRepo;

    public GraphDto loadGraph(Long caseId) {
        return new GraphDto(
            nodeRepo.findByCaseId(caseId),
            linkRepo.findByCaseId(caseId),
            caseId
        );
    }

    public GraphDto saveGraph(GraphDto graphDto) {
        Long caseId = graphDto.getCaseId();

        nodeRepo.deleteByCaseId(caseId);
        linkRepo.deleteByCaseId(caseId);

        // 1️⃣ Save nodes
        List<Node> savedNodes = nodeRepo.saveAll(graphDto.getNodes());

        // 2️⃣ Map index → actual DB ID
        Map<Integer, Long> indexToId = new HashMap<>();
        for (int i = 0; i < savedNodes.size(); i++) {
            indexToId.put(i, savedNodes.get(i).getNodeId());
        }

        // 3️⃣ Fix links
        for (Link link : graphDto.getLinks()) {
            link.setNodeIdFrom(indexToId.get(link.getNodeIdFrom().intValue()));
            link.setNodeIdTo(indexToId.get(link.getNodeIdTo().intValue()));
        }

        // 4️⃣ Save links
        linkRepo.saveAll(graphDto.getLinks());

        return graphDto;
    }

    // public Node addNode(Node node) {
    //     boolean exists = nodeRepo.existsByCaseIdAndNodeTypeAndNodeReference(
    //         node.getCaseId(),
    //         node.getNodeType(),
    //         node.getNodeReference()
    //     );
    //     if (exists) {
    //         throw new IllegalStateException("Node already exists in graph");
    //     }
    //     return nodeRepo.save(node);
    // }

    // public Link addLink(Link link) {
    //     return linkRepo.save(link);
    // }

    // public void deleteNode(Long caseId, Long nodeId) {
    //     linkRepo.deleteByCaseIdAndNodeIdFromOrNodeIdTo(caseId, nodeId, nodeId);
    //     nodeRepo.deleteById(nodeId);
    // }

    // public void deleteLink(Long caseId, Long linkId) {
    //     linkRepo.deleteById(linkId);
    // }

}
