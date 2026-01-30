package com.forensic.dto;
import com.forensic.entity.Node;
import com.forensic.entity.Link;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class GraphDto {
    private List<Node> nodes;
    private List<Link> links;
}

