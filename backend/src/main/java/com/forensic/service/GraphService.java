package com.forensic.service;

import com.forensic.entity.Node;
import com.forensic.entity.Link;
import com.forensic.dto.GraphDto;
import com.forensic.repository.NodeRepository;
import com.forensic.repository.LinkRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class GraphService {

    private final NodeRepository nodeRepo;
    private final LinkRepository linkRepo;

    public GraphDto loadGraph(String caseKey) {
        return new GraphDto(
            nodeRepo.findByCaseKey(caseKey),
            linkRepo.findByCaseKey(caseKey)
        );
    }

    public Node addNode(Node node) {
        boolean exists = nodeRepo.existsByCaseKeyAndNodeTypeAndNodeReference(
            node.getCaseKey(),
            node.getNodeType(),
            node.getNodeReference()
        );
        if (exists) {
            throw new IllegalStateException("Node already exists in graph");
        }
        return nodeRepo.save(node);
    }

    public Link addLink(Link link) {
        return linkRepo.save(link);
    }

    public void deleteNode(String caseKey, Long nodeId) {
        linkRepo.deleteByCaseKeyAndNodeIdFromOrNodeIdTo(caseKey, nodeId, nodeId);
        nodeRepo.deleteById(nodeId);
    }

    public void deleteLink(String caseKey, Long linkId) {
        linkRepo.deleteById(linkId);
    }
}
