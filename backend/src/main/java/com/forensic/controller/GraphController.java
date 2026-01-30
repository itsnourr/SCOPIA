package com.forensic.controller;

import com.forensic.entity.Node;
import com.forensic.entity.Link;
import org.springframework.web.bind.annotation.*;

import com.forensic.dto.GraphDto;
import com.forensic.service.GraphService;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/graph/{caseKey}")
@RequiredArgsConstructor
public class GraphController {

    private final GraphService graphService;

    @GetMapping("/")
    public GraphDto load(@PathVariable String caseKey) {
        return graphService.loadGraph(caseKey);
    }

    @PostMapping("/nodes")
    public Node addNode(
        @PathVariable String caseKey,
        @RequestBody Node node
    ) {
        node.setCaseKey(caseKey);
        return graphService.addNode(node);
    }

    @PostMapping("/links")
    public Link addLink(
        @PathVariable String caseKey,
        @RequestBody Link link
    ) {
        link.setCaseKey(caseKey);
        return graphService.addLink(link);
    }

    @DeleteMapping("/nodes/{nodeId}")
    public void deleteNode(
        @PathVariable String caseKey,
        @PathVariable Long nodeId
    ) {
        graphService.deleteNode(caseKey, nodeId);
    }

    @DeleteMapping("/links/{linkId}")
    public void deleteLink(
        @PathVariable String caseKey,
        @PathVariable Long linkId
    ) {
        graphService.deleteLink(caseKey, linkId);
    }
}
